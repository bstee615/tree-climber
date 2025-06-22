interface LanguageSelectorProps {
  language: string;
  onLanguageChange: (language: string) => void;
}

const SUPPORTED_LANGUAGES = [
  { value: 'c', label: 'C' },
  { value: 'java', label: 'Java' },
  { value: 'python', label: 'Python' }
] as const;

function LanguageSelector({ language, onLanguageChange }: LanguageSelectorProps) {
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

export default LanguageSelector;
