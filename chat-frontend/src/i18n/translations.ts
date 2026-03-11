export const translations = {
  fr: {
    // Header
    chatTitle: 'World Bank',
    chatName: 'WB Assistant',
    statusOnline: 'En ligne · Données 2014–2023',
    clearConversation: 'Réinitialiser',
    minimize: 'Réduire',
    open: 'Ouvrir',
    switchToEnglish: 'Switch to English',
    switchToFrench: 'Passer en Français',

    // Greeting
    greetingIntro: 'Bonjour 👋 Je suis <strong>WB Assistant</strong>, votre guide des données de la <strong>Banque Mondiale</strong>.',
    greetingDetails: 'Je peux vous renseigner sur le PIB, la croissance, l\'inflation, la population, l\'éducation, la santé, l\'énergie et plus encore, pour <strong>35+ pays</strong> de 2014 à 2023.',
    greetingPrompt: 'Cliquez sur une suggestion ou posez votre question ci-dessous.',

    // Quick Replies
    quickReplies: [
      { icon: '📊', label: 'PIB de la France en 2023' },
      { icon: '🌍', label: 'Population mondiale 2023' },
      { icon: '💹', label: 'Croissance économique USA' },
      { icon: '🎓', label: 'Taux de scolarisation en Afrique' },
      { icon: '🌿', label: 'Émissions CO₂ par pays' },
    ],

    // Suggestions
    suggestionsPrompt: 'Vous pourriez aussi demander :',
    contextualSuggestions: [
      { icon: '📈', label: 'Quelle est la croissance du PIB de la Chine ?' },
      { icon: '💹', label: 'Quel est le taux d\'inflation en Inde ?' },
      { icon: '👥', label: 'Quelle est la population du Brésil ?' },
      { icon: '🏥', label: 'Quel est le taux de mortalité infantile au Nigeria ?' },
      { icon: '🎓', label: 'Quel est le taux de scolarisation au Maroc ?' },
      { icon: '⚡', label: 'Consommation d\'énergie per capita au Japon ?' },
      { icon: '🌳', label: 'Quelle est la superficie forestière en Russie ?' },
      { icon: '📱', label: 'Taux d\'internet en Afrique ?' },
      { icon: '📊', label: 'PIB per capita de l\'Allemagne ?' },
      { icon: '🌍', label: 'Taux de chômage en Espagne ?' },
    ],

    // Composer
    composerPlaceholder: 'Posez votre question sur les données de la Banque Mondiale…',
    sendButton: 'Envoyer',

    // Callout
    calloutMessage: '💬 Posez vos questions sur la Banque Mondiale',

    // Errors
    errorMessage: '⚠️ Erreur : impossible de joindre le serveur.',
    noResponse: 'Désolé, pas de réponse.',
  },

  en: {
    // Header
    chatTitle: 'World Bank',
    chatName: 'WB Assistant',
    statusOnline: 'Online · Data 2014–2023',
    clearConversation: 'Clear',
    minimize: 'Minimize',
    open: 'Open',
    switchToEnglish: 'Switch to English',
    switchToFrench: 'Passer en Français',

    // Greeting
    greetingIntro: 'Hello 👋 I\'m <strong>WB Assistant</strong>, your guide to <strong>World Bank</strong> data.',
    greetingDetails: 'I can provide information on GDP, growth, inflation, population, education, health, energy and more, for <strong>35+ countries</strong> from 2014 to 2023.',
    greetingPrompt: 'Click a suggestion below or ask your question.',

    // Quick Replies
    quickReplies: [
      { icon: '📊', label: 'France GDP in 2023' },
      { icon: '🌍', label: 'World population 2023' },
      { icon: '💹', label: 'USA economic growth' },
      { icon: '🎓', label: 'School enrollment in Africa' },
      { icon: '🌿', label: 'CO₂ emissions by country' },
    ],

    // Suggestions
    suggestionsPrompt: 'You might also ask:',
    contextualSuggestions: [
      { icon: '📈', label: 'What is China\'s GDP growth rate?' },
      { icon: '💹', label: 'What is the inflation rate in India?' },
      { icon: '👥', label: 'What is Brazil\'s population?' },
      { icon: '🏥', label: 'What is the infant mortality rate in Nigeria?' },
      { icon: '🎓', label: 'What is the school enrollment rate in Morocco?' },
      { icon: '⚡', label: 'Energy consumption per capita in Japan?' },
      { icon: '🌳', label: 'What is Russia\'s forest area?' },
      { icon: '📱', label: 'Internet penetration rate in Africa?' },
      { icon: '📊', label: 'Germany\'s GDP per capita?' },
      { icon: '🌍', label: 'Unemployment rate in Spain?' },
    ],

    // Composer
    composerPlaceholder: 'Ask your question about World Bank data…',
    sendButton: 'Send',

    // Callout
    calloutMessage: '💬 Ask your questions about the World Bank',

    // Errors
    errorMessage: '⚠️ Error: unable to reach the server.',
    noResponse: 'Sorry, no response available.',
  },
}

export type Language = 'fr' | 'en'
export type TranslationKey = keyof typeof translations.fr

export function t(lang: Language, key: TranslationKey): any {
  return translations[lang]?.[key] ?? translations.fr[key]
}
