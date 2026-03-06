"""
FAQ Handler - Deterministic responses for common World Bank questions
Separates FAQ logic from main application routing
(Pattern aligné sur le projet AAA)
"""
import re
from typing import Optional


class FAQHandler:
    """Handles deterministic FAQ responses for common questions"""

    def __init__(self):
        # Compile patterns once at initialization
        self.greetings_pattern = re.compile(
            r'^(bonjour|bonsoir|salut|hello|hi|hey|coucou)[\s!.?]*$',
            re.IGNORECASE
        )

        self.farewell_pattern = re.compile(
            r'\b(merci|au revoir|bonne journée|thanks?|thank you|goodbye|bye|have a good day)\b',
            re.IGNORECASE
        )

        self.privacy_pattern = re.compile(
            r'\b(rgpd|gdpr|confidentialit|privacy|données personnelles|personal data|'
            r'stock(e|es|er|ons|ez|ent|age)?|store[sd]?|storing|'
            r'sauvegard(e|es|er|ons|ez|ent)?|enregistr(e|es|er|ons|ez|ent)?|'
            r'conserv(e|es|er|ons|ez|ent)?|supprim(e|es|er|ons|ez|ent)?|'
            r'delet(e|es|ing)?|politique de confidentialité|privacy policy)\b',
            re.IGNORECASE
        )

        self.indicators_pattern = re.compile(
            r'\b(quels? indicateurs?|which indicators?|available indicators?|indicateurs disponibles?|'
            r'list.*indicators?)\b',
            re.IGNORECASE
        )

        self.sources_pattern = re.compile(
            r'\b(source|sources|d\'où viennent|where.*data come|data source)\b',
            re.IGNORECASE
        )

    def check_faq(self, query: str, lang: str = "fr") -> Optional[str]:
        """
        Check if query matches a FAQ pattern and return deterministic response.

        Args:
            query: User query (raw, unnormalized)
            lang: Language code ('fr' or 'en')

        Returns:
            HTML response string if FAQ matched, None otherwise
        """
        query_lower = query.lower().strip()

        # Check greetings
        if self.greetings_pattern.match(query_lower):
            return self._get_greeting_response(lang)

        # Check farewells
        if self.farewell_pattern.search(query_lower) and len(query_lower.split()) <= 8:
            return self._get_farewell_response(lang)

        # Check RGPD/privacy
        if self.privacy_pattern.search(query_lower):
            return self._get_privacy_response(lang)

        # Check available indicators
        if self.indicators_pattern.search(query_lower):
            return self._get_indicators_response(lang)

        # Check data sources
        if self.sources_pattern.search(query_lower) and len(query_lower.split()) <= 6:
            return self._get_sources_response(lang)

        return None

    def _get_greeting_response(self, lang: str) -> str:
        if lang.lower().startswith("en"):
            return (
                "<p>👋 Hello! I'm your World Bank data assistant.</p>"
                "<p>I can help you with:</p>"
                "<ul>"
                "<li>Economic indicators (GDP, GNI, inflation...)</li>"
                "<li>Social data (population, education, health...)</li>"
                "<li>Environmental statistics (CO2 emissions, forests...)</li>"
                "<li>Country comparisons and trends</li>"
                "</ul>"
                "<p><b>What would you like to know?</b></p>"
            )
        return (
            "<p>👋 Bonjour ! Je suis votre assistant spécialisé en données de la Banque Mondiale.</p>"
            "<p>Je peux vous aider avec :</p>"
            "<ul>"
            "<li>Indicateurs économiques (PIB, RNB, inflation...)</li>"
            "<li>Données sociales (population, éducation, santé...)</li>"
            "<li>Statistiques environnementales (émissions CO2, forêts...)</li>"
            "<li>Comparaisons entre pays et tendances</li>"
            "</ul>"
            "<p><b>Quelle est votre question ?</b></p>"
        )

    def _get_farewell_response(self, lang: str) -> str:
        if lang.lower().startswith("en"):
            return (
                "<p>You're welcome! Feel free to come back if you have more questions "
                "about World Bank development data. Have a great day!</p>"
            )
        return (
            "<p>Avec plaisir ! N'hésitez pas à revenir si vous avez d'autres questions "
            "sur les données de développement de la Banque Mondiale. Bonne journée !</p>"
        )

    def _get_privacy_response(self, lang: str) -> str:
        if lang.lower().startswith("en"):
            return (
                "<p>This chatbot does not store personal data beyond the current conversation. "
                "Your messages are processed to generate responses but are not saved long-term.</p>"
                "<p>For the official World Bank privacy policy, please visit: "
                "<a href='https://www.worldbank.org/en/about/legal/privacy-notice'>World Bank Privacy Notice</a>.</p>"
            )
        return (
            "<p>Cet agent conversationnel ne stocke pas de données personnelles au-delà de la conversation en cours. "
            "Vos messages sont traités pour générer des réponses mais ne sont pas sauvegardés à long terme.</p>"
            "<p>Pour la politique de confidentialité officielle de la Banque Mondiale, veuillez consulter : "
            "<a href='https://www.worldbank.org/en/about/legal/privacy-notice'>Avis de confidentialité de la Banque Mondiale</a>.</p>"
        )

    def _get_indicators_response(self, lang: str) -> str:
        if lang.lower().startswith("en"):
            return (
                "<p>Here are the <b>main indicators</b> available in our database:</p>"
                "<ul>"
                "<li><b>NY.GDP.MKTP.CD</b> — GDP (current US$)</li>"
                "<li><b>SP.POP.TOTL</b> — Total population</li>"
                "<li><b>SL.UEM.TOTL.ZS</b> — Unemployment rate (% of labor force)</li>"
                "<li><b>EN.ATM.CO2E.PC</b> — CO2 emissions (metric tons per capita)</li>"
                "<li><b>SE.PRM.ENRR</b> — Primary school enrollment rate</li>"
                "<li><b>SH.DYN.MORT</b> — Infant mortality rate (per 1,000)</li>"
                "</ul>"
                "<p>For the full catalogue: <a href='https://data.worldbank.org/indicator'>World Bank Indicators</a></p>"
                "<p><b>Which indicator interests you?</b></p>"
            )
        return (
            "<p>Voici les <b>principaux indicateurs</b> disponibles dans notre base :</p>"
            "<ul>"
            "<li><b>NY.GDP.MKTP.CD</b> — PIB (USD courants)</li>"
            "<li><b>SP.POP.TOTL</b> — Population totale</li>"
            "<li><b>SL.UEM.TOTL.ZS</b> — Taux de chômage (% pop. active)</li>"
            "<li><b>EN.ATM.CO2E.PC</b> — Émissions CO2 (tonnes/habitant)</li>"
            "<li><b>SE.PRM.ENRR</b> — Taux de scolarisation primaire</li>"
            "<li><b>SH.DYN.MORT</b> — Mortalité infantile (‰)</li>"
            "</ul>"
            "<p>Catalogue complet : <a href='https://data.worldbank.org/indicator'>Indicateurs Banque Mondiale</a></p>"
            "<p><b>Quel indicateur vous intéresse ?</b></p>"
        )

    def _get_sources_response(self, lang: str) -> str:
        if lang.lower().startswith("en"):
            return (
                "<p>All data comes from the <b>World Bank Open Data API</b>:</p>"
                "<ul>"
                "<li><a href='https://data.worldbank.org/'>data.worldbank.org</a></li>"
                "<li>License: <a href='https://creativecommons.org/licenses/by/4.0/'>CC BY 4.0</a></li>"
                "</ul>"
                "<p><b>Would you like to query a specific indicator?</b></p>"
            )
        return (
            "<p>Toutes les données proviennent de l'<b>API Open Data de la Banque Mondiale</b> :</p>"
            "<ul>"
            "<li><a href='https://data.worldbank.org/'>data.worldbank.org</a></li>"
            "<li>Licence : <a href='https://creativecommons.org/licenses/by/4.0/'>CC BY 4.0</a></li>"
            "</ul>"
            "<p><b>Souhaitez-vous interroger un indicateur précis ?</b></p>"
        )


# Singleton instance
faq_handler = FAQHandler()
