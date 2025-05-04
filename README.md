# Projekt 55 - AI-Driven Innehållsplattform

Projekt 55 är en webbapplikation som använder AI för att hjälpa företag skapa engagerande och personligt innehåll över flera plattformar. Applikationen integrerar med Claude AI för intelligenta konversationer och innehållsgenerering, samtidigt som den erbjuder trendanalys och nyhetssammanfattningar för content creation.

## Funktioner

- **AI Chattassistent**
  - Personliga konversationer baserade på företagsprofil
  - Konfigurerbar kommunikationsstil
  - Kontextmedvetna svar
  - Hantering av chatthistorik

- **Innehållsgenerering**
  - Plattformsspecifik innehållsoptimering
  - Anpassningsbar ton och stil
  - Flera längdalternativ för innehåll
  - Sammanfattning av nyhetsinnehåll

- **Trendanalys**
  - Realtidsspårning av trender
  - Geografisk intressekartläggning
  - Relaterade ämnen och frågor
  - Nyhetsintegration

- **Företagsinställningar**
  - Anpassningsbar företagsprofil
  - Målgruppsdefinition
  - Varumärkesröstkonfiguration
  - Branschspecifik optimering

## Installation

1. Skapa och aktivera en virtuell miljö:
```bash
python -m venv venv
venv\Scripts\activate  # För Windows
```

2. Installera beroenden:
```bash
pip install -r requirements.txt
```

3. Konfigurera miljövariabler:
Skapa en .env fil och konfigurera dina miljövariabler

4. Starta applikationen:
```bash
python run.py
```

## Miljövariabler

Skapa en `.env` fil med följande variabler:
```
FLASK_APP=run.py
FLASK_ENV=development
ANTHROPIC_API_KEY=din_api_nyckel_här
SECRET_KEY=din_hemliga_nyckel_här
DATABASE_URL=sqlite:///project55.db
```

## Användning

1. Registrera ett nytt konto
2. Konfigurera din företagsprofil i Inställningar
3. Starta en ny chatt med anpassade konfigurationer
4. Analysera trender och generera innehåll
5. Visa och hantera chatthistorik

## Testning

Kör testerna med pytest:
```bash
pytest
```

# Kursmoment som jag valt att inkludera

### ✅ A. Säker programmering
- **Lösenordshashning**: Implementerat i User-modellen med Werkzeugs säkra hashningsfunktioner. Lösenord hashas vid registrering och verifieras vid inloggning.
- **Rate limiting**: Implementerat på känsliga endpoints som login och API-anrop. Använder Flask-Limiter för att begränsa antal förfrågningar.
- **Säker sessionshantering**: Använder Flask-Login för säker autentisering och sessionhantering. Automatisk session-timeout och säker cookie-hantering.
- **Input validering**: Omfattande validering av användarinput genom WTForms. Särskilt strikt validering av lösenord vid registrering.

### ✅ B. Avancerad datahantering
- **Pandas för trendanalys**: Används i fetch_trend_summary() för att analysera och bearbeta trenddata från Google Trends API.
- **DataFrame-hantering**: Bearbetar rådata från APIs till strukturerade DataFrames för analys av trender och geografisk data.
- **Databearbetning**: Transformerar och filtrerar trenddata för att identifiera mönster och relevanta insikter.
- **Statistiska beräkningar**: Utför beräkningar på trenddata som medelvärden, max-värden och trendanalys över tid.
- **Geografisk dataanalys**: Analyserar och visualiserar geografisk distribution av trender med Pandas geografiska funktioner.

### ✅ C. API-integrationer
- **Anthropic Claude AI**: Integration med Claude AI för kontextmedveten innehållsgenerering och chattfunktionalitet.
- **Google Trends API**: Realtidsintegration via pytrends för att hämta och analysera aktuella trender.
- **GNews API**: Integrerar med GNews för att hämta relevanta nyhetsartiklar och sammanfattningar.
- **REST API-endpoints**: API-endpoints för alla huvudfunktioner med proper felhantering.

### ✅ D. Webbutveckling
- **Flask-ramverk**: Strukturerad applikation med Flask, använder blueprints för modulär arkitektur.
- **Jinja2 templates**: Avancerad template-hierarki med arv och återanvändbara komponenter.
- **AJAX-anrop**: Asynkron datahämtning för sömlös användarupplevelse i trendanalys och chat.

### ✅ F. Enhetstestning och felsökning
- **pytest test suite**: Omfattande tester som täcker alla kritiska funktioner.
- **Fixtures**: Återanvändbara testfixtures för databas och autentisering.
- **Omfattande logging**: Strukturerad logging av alla viktiga operationer för felsökning och övervakning.
- **Strukturerad felhantering**: Konsekvent felhantering med informativa felmeddelanden och återhämtning.
- **Test coverage**: God testtäckning av kritiska komponenter med automatiserade tester.

### ✅ H. SQL med Python
- **SQLAlchemy ORM**: Robust databashantering med SQLAlchemy för alla modeller.
- **Databasmodeller**: Väldefinierade modeller med relationer för användare, chattar och företagsinformation.
- **CRUD-operationer**: Fullständig implementering av Create, Read, Update, Delete-operationer.