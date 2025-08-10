import React from 'react';

interface LanguageSelectorProps {
  language: string;
  onLanguageChange: (language: string) => void;
}

const SUPPORTED_LANGUAGES = [
  { value: 'c', label: 'C' },
  { value: 'java', label: 'Java' },
] as const;

export function loadLanguage(): string {
  // Load the selected language from localStorage or default to 'c'
  let language = localStorage.getItem('tree_climber_selected_language');
  if (!language) {
    language = 'c'; // Default to 'c' if no language is set
  }
  localStorage.setItem('tree_climber_selected_language', language);
  return language;
}

export function LanguageSelector({ language, onLanguageChange }: LanguageSelectorProps) {
  // Save selected language to localStorage whenever it changes
  React.useEffect(() => {
    localStorage.setItem('tree_climber_selected_language', language);
  }, [language]);

  return (
    <div className="app-container">
      <label htmlFor="language-select">Select Language:</label>
      <select 
        id="language-select"
        onChange={(e) => onLanguageChange(e.target.value)} 
        value={language}
      >
        {SUPPORTED_LANGUAGES.map(({ value, label }) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
    </div>
  );
}
