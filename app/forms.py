from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


# Form som visas i /settings
class CompanySettingsForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    industry = SelectField('Industry', choices=[
        ('technology', 'Technology'),
        ('healthcare', 'Healthcare'),
        ('finance', 'Finance'),
        ('retail', 'Retail'),
        ('education', 'Education'),
        ('manufacturing', 'Manufacturing'),
        ('media', 'Media & Entertainment'),
        ('real_estate', 'Real Estate'),
        ('automotive', 'Automotive'),
        ('hospitality', 'Hospitality & Tourism'),
        ('consulting', 'Consulting'),
        ('energy', 'Energy & Utilities'),
        ('telecom', 'Telecommunications'),
        ('agriculture', 'Agriculture'),
        ('construction', 'Construction'),
        ('transportation', 'Transportation & Logistics'),
        ('pharmaceuticals', 'Pharmaceuticals'),
        ('gaming', 'Gaming'),
        ('sports', 'Sports & Recreation'),
        ('non_profit', 'Non-Profit'),
        ('other', 'Other')
    ])
    background = TextAreaField('Company Background', 
        validators=[DataRequired()],
        description="Brief description of your company's history, mission, and values")
    target_audience = TextAreaField('Target Audience',
        validators=[DataRequired()],
        description="Describe your ideal customer or target market")
    brand_voice = SelectField('Brand Voice', choices=[
        ('professional', 'Professional & Formal'),
        ('friendly', 'Friendly & Casual'),
        ('innovative', 'Innovative & Tech-Savvy'),
        ('authoritative', 'Authoritative & Expert'),
        ('playful', 'Playful & Fun')
    ])
    key_values = StringField('Key Values',
        description="Enter company values separated by commas (e.g., Innovation, Quality, Customer Focus)")
    submit = SubmitField('Save Settings')

# Form som visas i /login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

# Form som visas i /register
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=20)
    ])
    email = EmailField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Create Account')

# Form som visas när man genererar content från nyhetssummering
class NewsContentForm(FlaskForm):
    content_type = SelectField('Content Type', choices=[
        ('share', 'Share the News'),
        ('comment', 'Comment on the News'),
        ('opinion', 'Express Opinion'),
        ('humor', 'Humorous Take'),
        ('analysis', 'Deep Analysis'),
        ('tldr', 'TL;DR Summary'),
        ('counterpoint', 'Present Counterpoint')
    ], validators=[DataRequired()])
    
    platform = SelectField('Platform', choices=[
        ('general', 'General'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram')
    ], validators=[DataRequired()])
    
    tone_style = SelectField('Tone Style', choices=[
        ('professional', 'Professional'),
        ('casual', 'Casual'),
        ('friendly', 'Friendly'),
        ('formal', 'Formal')
    ], validators=[DataRequired()])
    
    length = SelectField('Content Length', choices=[
        ('short', 'Short'),
        ('medium', 'Medium'),
        ('long', 'Long')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Generate Content')

# Form för /trends
class TrendAnalysisForm(FlaskForm):
    keywords = StringField('Keywords', 
        validators=[DataRequired()],
        description="Enter keywords separated by commas (e.g., AI, Machine Learning, Data Science)")
    submit = SubmitField('Analyze Trends')

# Form för /config_chat
class ChatConfigForm(FlaskForm):
    tone_style = SelectField('Tone Style', choices=[
        ('professional', 'Professional'),
        ('casual', 'Casual'),
        ('friendly', 'Friendly'),
        ('formal', 'Formal')
    ], validators=[DataRequired()])
    
    platform = SelectField('Platform', choices=[
        ('general', 'General'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram')
    ], validators=[DataRequired()])
    
    length = SelectField('Content Length', choices=[
        ('short', 'Short'),
        ('medium', 'Medium'),
        ('long', 'Long')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Start Chat')

    def populate_from_config(self, config):
        """Populate form from existing chat config"""
        if config:
            self.tone_style.data = config.get('tone_style', 'professional')
            self.platform.data = config.get('platform', 'general')
            self.length.data = config.get('length', 'medium')