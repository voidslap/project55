from datetime import datetime
from flask import render_template, request, redirect, url_for, session, Blueprint, flash, jsonify, current_app, abort
from app import db
from app.models import User, Chat, Message
from flask import current_app as app
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .utils import fetch_trend_summary, get_hot_trends, fetch_news_summary, get_combined_news_summary, send_message_to_anthropic
from .forms import *
from .models import Company
from .prompts import get_news_content_prompt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re

# Skapar en Blueprint
bp = Blueprint('main', __name__)

# Limiter för att begränsa antalet förfrågningar
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["2000 per day", "200 per hour"]
)

@bp.route('/')
def startpage():
    return render_template('index.html')


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute") # Begränsar antalet login förfrågningar till 5 per minut
def login():
    form = LoginForm()  # Skapar LoginForm instance
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.hashed_password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        flash('Invalid username or password')
    
    return render_template('login.html', form=form)  # Pass form to template


# Route för dashboard
@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# Route för att registrera en ny användare
@bp.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Kollar om användarnamn redan finns
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists")
            return redirect(url_for("main.register"))

        # Kollar om email redan finns
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered")
            return redirect(url_for("main.register"))

        # Lösenord validering (Kollar så att lösenordet uppfyller kraven)
        password = form.password.data
        if len(password) < 8:
            flash("Password must be at least 8 characters")
            return redirect(url_for("main.register"))
        
        if not any(c.isupper() for c in password):
            flash("Password must contain at least one uppercase letter")
            return redirect(url_for("main.register"))
        
        if not any(c.islower() for c in password):
            flash("Password must contain at least one lowercase letter")
            return redirect(url_for("main.register"))
        
        if not any(c.isdigit() for c in password):
            flash("Password must contain at least one number")
            return redirect(url_for("main.register"))
        
        if not any(c in "!@#$%^&*" for c in password):
            flash("Password must contain at least one special character (!@#$%^&*)")
            return redirect(url_for("main.register"))

        # Kollar så att lösenorden matchar
        if form.password.data != form.confirm_password.data:
            flash("Passwords must match")
            return redirect(url_for("main.register"))


        # Om alla valideringar är godkända, skapa en ny användare
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            hashed_password=hashed_password
        )
        
        db.session.add(new_user) # Lägger till användaren i databasen
        db.session.commit() # Sparar ändringarna i databasen
        
        flash("Registration successful! Please log in.")
        return redirect(url_for("main.login"))

    return render_template("register.html", form=form)

# Loggar ut användaren
@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.login"))


# Route för att skapa en ny chat
@bp.route("/config_chat")
@bp.route("/config_chat/<int:chat_id>") # Route för att kunna konfigurera en befintlig chat
@login_required
def config_chat(chat_id=None): # Tar emot ett chat_id som parameter (None om ny chat skapas)
    form = ChatConfigForm()
    
    if chat_id:
        chat = Chat.query.get_or_404(chat_id)
        if chat.user_id != current_user.id: # Kollar så att användaren äger chatten
            abort(403)
        current_config = chat.get_config() # Hämtar konfigurationen för chatten
        form.populate_from_config(current_config)
    else:
        # Rensar session när ny chat skapas
        session.pop('current_chat_id', None)
        chat_id = None

   # Renderar config_chat.html med chat_id och konfigurationen 
    return render_template(
        "config_chat.html", 
        form=form,
        chat_id=chat_id
    )


# Route för att spara konfigurationen för en chat
@bp.route("/save_chat_config", methods=['POST'])
@login_required
def save_chat_config():
    chat_id = request.form.get('chat_id')
    config = {
        'tone_style': request.form.get('tone_style'),
        'platform': request.form.get('platform'),
        'length': request.form.get('length')
    }
    
    try:
        if chat_id and chat_id.isdigit():
            chat = Chat.query.get_or_404(int(chat_id))
            if chat.user_id != current_user.id:
                abort(403)
            chat.set_config(config)
        else:
            # Rensar session när ny chat skapas
            session.pop('current_chat_id', None)
            
            # Kollar så att användaren inte har för många chats (Max 10)
            enforce_chat_limit(current_user.id)
            
            # Skapar ny chat
            chat = Chat(
                title="New Chat",
                user_id=current_user.id
            )
            chat.set_config(config)
            db.session.add(chat) # Lägger till chatten i databasen
        
        db.session.commit() # Sparar ändringarna i databasen
        
        # Om chat_id finns, skicka användaren till chatten
        if chat_id:
            return redirect(url_for('main.chat', chat_id=chat.id))
        else:
            session['current_chat_id'] = chat.id
            return redirect(url_for('main.chat'))
    
    # Felhantering om något går fel
    except Exception as e:
        current_app.logger.error(f"Error in save_chat_config: {str(e)}")
        flash('An error occurred while saving chat configuration', 'error')
        return redirect(url_for('main.config_chat')) # Returnera användaren till config_chat.html


# Route för att starta en chat
@bp.route("/start_chat", methods=['POST'])
@login_required
def start_chat():
    # Sparar chat konfigurationen i session
    session['chat_config'] = {
        'tone_style': request.form.get('tone_style'),
        'platform': request.form.get('platform'),
        'length': request.form.get('length')
    }
    
    # Om användaren vill återgå till en tidigare chat, return here
    return_to_chat = request.form.get('return_to_chat')
    if return_to_chat and return_to_chat.isdigit():
        return redirect(url_for('main.load_chat', chat_id=int(return_to_chat)))
    
    return redirect(url_for('main.chat'))

# Route for chat history
@bp.route("/chat_history")
@login_required
def chat_history(): # Returnerar de 10 senaste chattarna för användaren
    chats = Chat.query.filter_by(user_id=current_user.id)\
        .order_by(Chat.updated_at.desc())\
        .limit(10)\
        .all()
    return render_template("chat_history.html", chats=chats)

# Route för att ladda en tidigare chat
@bp.route("/chat/<int:chat_id>")
@login_required
def load_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        abort(403)
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    session['chat_config'] = chat.get_config()
    session['current_chat_id'] = chat_id
    return render_template("chat.html", messages=messages, chat=chat)

# Route för att ladda en ny chat
@bp.route("/chat", methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
            
        message = data['message']
        chat_id = session.get('current_chat_id')
        
        try:
            chat = Chat.query.get(chat_id) if chat_id else None
            
            if not chat or chat.user_id != current_user.id:
                # Först kontrollera att användaren inte har för många chattar
                enforce_chat_limit(current_user.id)
                # Sen skapa ny chat
                chat = Chat(
                    title=message[:97] + "..." if len(message) > 100 else message,
                    user_id=current_user.id
                )
                db.session.add(chat)
                db.session.commit()
                session['current_chat_id'] = chat.id

            # Hämta svar från Anthropic
            bot_response = send_message_to_anthropic(
                message=message,
                model_name="claude-3-sonnet-20240229",
                user=current_user,
                chat=chat
            )
            
            # Spara meddelanden i databasen
            user_message = Message(content=message, chat_id=chat.id, is_bot=False)
            bot_message = Message(content=bot_response, chat_id=chat.id, is_bot=True)
            
            db.session.add_all([user_message, bot_message])
            chat.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({'response': bot_response})
            
        except Exception as e:
            current_app.logger.error(f"Chat error: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'An error occurred processing your message'}), 500

    # Laddar chat.html med meddelanden från databasen
    chat_id = session.get('current_chat_id')
    chat = None
    messages = []
    initial_message = request.args.get('initial_message')
    
    if chat_id:
        chat = Chat.query.get(chat_id)
        if chat and chat.user_id == current_user.id:
            messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    
    if initial_message:
        try:
            # Lägg inte till initial message i listan med visade meddelanden
            # Hämta bara svar från Anthropic direkt
            bot_response = send_message_to_anthropic(
                message=initial_message,
                model_name="claude-3-sonnet-20240229",
                user=current_user,
                chat=chat
            )
            # Sparar båda meddelanden i databasen
            user_msg = Message(content=initial_message, chat_id=chat.id, is_bot=False)
            bot_msg = Message(content=bot_response, chat_id=chat.id, is_bot=True)
            db.session.add_all([user_msg, bot_msg])
            db.session.commit()
            
            # Visar bara botens svar i chat.html
            messages.append({'content': bot_response, 'is_bot': True})
        except Exception as e:
            current_app.logger.error(f"Error processing initial message: {str(e)}")
    
    return render_template('chat.html', 
                         messages=messages, 
                         chat=chat)

# Route för att radera en chat
@bp.route("/delete_chat/<int:chat_id>", methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        abort(403)
    
    try:
        db.session.delete(chat) # Tar bort chatten från databasen
        db.session.commit()
        return jsonify({'message': 'Chat deleted successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting chat: {str(e)}")
        db.session.rollback() # Ångra eventuella ändringar
        return jsonify({'error': 'Failed to delete chat'}), 500

def enforce_chat_limit(user_id, limit=10):
    """
    Ta bort äldre chattar och deras meddelanden om användaren har fler än gränsvärdet.
    Ska anropas INNAN en ny chatt skapas.
    """
    try:
        # Hämta alla användarens chattar sorterade efter uppdateringstid (äldst först)
        chats = Chat.query.filter_by(user_id=user_id)\
            .order_by(Chat.updated_at.asc())\
            .all()
        
        total_chats = len(chats)
        current_app.logger.info(f"User {user_id} has {total_chats} chats")
        
        if total_chats >= limit:
            # Beräkna hur många chattar som ska tas bort för att nå limit-1 
            # (gör plats för den nya chatten)
            chats_to_remove = total_chats - (limit - 1)
            # Hämta de äldsta chattarna som ska tas bort
            chats_to_delete = chats[:chats_to_remove]
            
            for chat in chats_to_delete:
                # Ta bort alla meddelanden för denna chatt
                Message.query.filter_by(chat_id=chat.id).delete()
                # Ta bort chatten
                db.session.delete(chat)
                current_app.logger.info(f"Deleted chat {chat.id} and its messages")
            
            db.session.commit()
            remaining = Chat.query.filter_by(user_id=user_id).count()
            current_app.logger.info(f"After cleanup: user {user_id} now has {remaining} chats")
            
    except Exception as e:
        current_app.logger.error(f"Error in enforce_chat_limit: {str(e)}")
        db.session.rollback()


# Route för att visa trender
@bp.route("/trends", methods=['GET', 'POST'])
@login_required
def trends():
    form = TrendAnalysisForm()
    hot_trends = get_hot_trends() # Hämtar populära trender
    
    if form.validate_on_submit():
        keywords = [k.strip() for k in form.keywords.data.split(',') if k.strip()]
        trends = fetch_trend_summary(keywords)
        return jsonify({'trends': trends})
        
    return render_template("trends.html", form=form, hot_trends=hot_trends)

# Route för att analysera trender
@bp.route("/analyze_trends", methods=['POST'])
@login_required
def analyze_trends():
    try:
        data = request.get_json()
        keywords = data.get('keywords', [])
        
        if not keywords:
            return jsonify({'error': 'No keywords provided'}), 400
        
        # Städar och validerar keywords
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',')]
        else:
            keywords = [k.strip() for k in keywords]
            
        keywords = [k for k in keywords if k]
        
        if not keywords:
            return jsonify({'error': 'No valid keywords provided'}), 400
        
        current_app.logger.debug(f"Analyzing trends for keywords: {keywords}")
        
        trends = fetch_trend_summary(keywords)
        
        if not trends:
            return jsonify({
                'trends': [{
                    'title': keyword,
                    'trend_summary': 'No trend data available for this topic',
                    'sentiment': 'NEUTRAL',
                    'key_points': [],
                    'average_interest': 0,
                    'peak_interest': 0,
                    'peak_date': 'N/A',
                    'news_articles': [],
                    'related_queries': []
                } for keyword in keywords]
            })
        
        return jsonify({'trends': trends}), 200
        
    except Exception as e:
        current_app.logger.error(f"Trend analysis error: {str(e)}")
        return jsonify({
            'error': 'Failed to analyze trends',
            'message': str(e)
        }), 500

# Route för att summera nyheter
@bp.route("/summarize_news", methods=['POST'])
@login_required
def summarize_news():
    try:
        data = request.get_json()
        keyword = data.get('keyword')
        
        if not keyword:
            return jsonify({'error': 'No keyword provided'}), 400

        # Hämta nyhetsartiklar
        news_articles = fetch_news_summary(keyword)
        
        if not news_articles:
            return jsonify({'error': 'No news articles found'}), 404

        # Generera en sammanfattning av nyhetsartiklarna
        summary = get_combined_news_summary(news_articles)
        
        # Returnera sammanfattningen
        return jsonify({'summary': summary})

    # Felhantering om något går fel
    except Exception as e:
        current_app.logger.error(f"News summarization error: {str(e)}")
        return jsonify({
            'error': 'Failed to summarize news',
            'message': str(e)
        }), 500

# Route för användarens inställningar
@bp.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    form = CompanySettingsForm()
    company = current_user.company

    # Fyller i formuläret med befintliga värden om användaren redan ställt in företagsinformation
    if request.method == 'GET' and company:
        form.company_name.data = company.company_name
        form.industry.data = company.industry
        form.background.data = company.background
        form.target_audience.data = company.target_audience
        form.brand_voice.data = company.brand_voice

    # Sparar användarens inställningar
    if form.validate_on_submit():
        if not company:
            company = Company(user_id=current_user.id)
            db.session.add(company)

        # Uppdaterar företagsinformationen
        company.company_name = form.company_name.data
        company.industry = form.industry.data
        company.background = form.background.data
        company.target_audience = form.target_audience.data
        company.brand_voice = form.brand_voice.data
        company.updated_at = datetime.utcnow()

        db.session.commit() # Sparar ändringarna i databasen
        flash('Company settings updated successfully', 'success')
        return redirect(url_for('main.settings'))

    return render_template('settings.html', form=form)


# Route för att konfigurera content som genereras från nyhetssummering
@bp.route("/news_content_config", methods=['GET', 'POST'])
@login_required
def news_content_config():
    form = NewsContentForm()
    summary = request.args.get('summary')
    title = request.args.get('title')
    
    if not summary or not title:
        return redirect(url_for('main.trends'))
    
    return render_template(
        'news_content_config.html',
        form=form,
        summary=summary,
        title=title
    )

# Route för att spara konfigurationen för content som genereras från nyhetssummering
@bp.route("/save_news_config", methods=['POST'])
@login_required
def save_news_config():
    form = NewsContentForm()
    
    if form.validate_on_submit():
        config = {
            'content_type': form.content_type.data,
            'platform': form.platform.data,
            'tone_style': form.tone_style.data,
            'length': form.length.data
        }
        
        summary = request.form.get('summary')
        title = request.form.get('title')
        
        if not summary or not title:
            flash('Missing required information', 'error')
            return redirect(url_for('main.trends'))
        
        # Enforce limit before creating new chat
        enforce_chat_limit(current_user.id)
        
        # Create new chat
        chat = Chat(
            title=f"News Content: {title[:50]}...",
            user_id=current_user.id
        )
        chat.set_config(config)
        db.session.add(chat)
        db.session.commit()
        
        session['current_chat_id'] = chat.id
        initial_message = get_news_content_prompt(summary, config)
        
        return redirect(url_for('main.chat', initial_message=initial_message))
    
    return redirect(url_for('main.trends'))