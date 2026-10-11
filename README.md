# 🌙 Quran Al-Kareem — القرآن الكريم

### Read the Quran. Understand Its Meaning. Follow Its Guidance.

A beautiful, responsive, and user-friendly Quran reading website built with **HTML5, CSS3, and Vanilla JavaScript**. Quran Al-Kareem provides a peaceful digital environment for reading the Holy Quran, understanding its meaning through translations, listening to recitations, saving favorite verses, and keeping track of daily Tasbih.

---


## ✨ Features

### 📖 Quran Reading
- Read the Holy Quran in its original Arabic text.
- Browse all 114 Surahs in the correct Quranic order.
- View Surah names, verse counts, and available Surah information.
- Navigate between previous and next Surahs.
- Jump to a specific verse.
- Search for Surahs using their names.

### 🌐 Multilingual Support
- **বাংলা (Bangla)** — Read Quran translations in Bengali.
- **English** — Read Quran translations in English.
- **العربية (Arabic)** — Arabic interface support where available.
- Switch between available interface and translation languages.
- Preserve the original Arabic Quranic text.

### 🔤 Translation Controls
- Show or hide translations using the top navigation toolbar.
- Read translations directly beneath Arabic verses.
- Keep the Arabic text visible when translations are hidden.
- Save translation visibility preferences.

### 🔊 Quran Audio
- Play Quran recitations when valid audio is available.
- Use audio playback controls.
- Display helpful messages when audio cannot be loaded.
- No automatic audio playback.

### 🔖 Bookmarks
- Save favorite Quranic verses.
- Remove saved bookmarks.
- View bookmarked verses.
- Return to a bookmarked verse.
- Keep bookmarks saved after refreshing the page.

### 📿 Digital Tasbih
- Count daily Dhikr with a digital counter.
- Read Arabic Dhikr and Bangla pronunciation.
- Choose from common Dhikr, including:
  - SubhanAllah
  - Alhamdulillah
  - Allahu Akbar
  - Astaghfirullah
- Undo the previous count.
- Reset the counter with confirmation.
- Preserve the counter using LocalStorage.

### 🎨 Theme Customization
- Switch between dark and light themes.
- Enjoy a dark reading interface with gold and emerald accents.
- Use a light theme with cream, ivory, and green colors.
- Save theme preferences between visits.

### 📱 Responsive Design
- Optimized for desktops, laptops, tablets, and smartphones.
- Responsive Surah sidebar and navigation.
- Readable Arabic typography on small screens.
- Accessible controls and clear focus indicators.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| HTML5 | Website structure and semantic markup |
| CSS3 | Styling, layouts, themes, and responsiveness |
| Vanilla JavaScript (ES6+) | Interactivity and application logic |
| AlQuran Cloud API | Quran text, Surah data, and translations |
| Fetch API | Retrieving Quran data |
| LocalStorage | Saving settings, bookmarks, and reading preferences |
| Google Fonts | Arabic and Bangla typography, when available |

---
## Netlify Link: https://quran-al-kareem-1.netlify.app
## Github Repository Link: https://github.com/nawrin30/Quran-Al-Kareem



## 📂 Project Structure

```text
quran-al-kareem/
│
├── index.html
├── README.md
│
├── css/
│   ├── style.css
│   ├── themes.css
│   └── responsive.css
│
├── js/
│   ├── config.js
│   ├── language.js
│   ├── quran.js
│   ├── app.js
│   ├── bookmarks.js
│   ├── audio.js
│   ├── tasbih.js
│   └── settings.js
│
└── assets/
    ├── images/
    └── icons/
```

---

## 🚀 Getting Started

Follow these steps to run the project locally.

### Prerequisites

- A modern web browser, such as Google Chrome, Microsoft Edge, or Firefox.
- [Visual Studio Code](https://code.visualstudio.com/).
- The Live Server extension for VS Code.
- An active internet connection for loading Quran data and other online resources.

### Installation

**Step 1: Download or clone the project**

Download the project ZIP and extract it, or clone the repository if it is hosted on GitHub.

```bash
git clone 
```

Replace `https://github.com/nawrin30/Quran-Al-Kareem` with your actual repository URL.

**Step 2: Open the project**

Open the extracted `quran-al-kareem` folder in Visual Studio Code.

**Step 3: Install Live Server**

Open the Extensions panel in VS Code, search for **Live Server**, and install it.

**Step 4: Run the website**

Open `index.html`, right-click inside the editor, and select **Open with Live Server**.

The website will open in your default browser.

> You can also use another local web server if you prefer. Some browser features and network requests may not work correctly when opening the HTML file directly using `file://`.

---

## 📡 Quran Data API

This project uses the AlQuran Cloud API to retrieve Quranic data.

**API base URL:**

`https://api.alquran.cloud/v1`

The application may use API endpoints for:

- Retrieving the list of Surahs.
- Loading Arabic Quranic text.
- Loading available Bangla and English translations.
- Retrieving available recitation data.

API availability and supported editions may change. Translation identifiers should be checked against the API's current supported editions.

**Important:** Quranic text and translations should be retrieved from reliable sources. The application should never silently replace a missing Bangla translation with English text or use machine-generated translations as a substitute for verified Quran translations.

---

## 💾 Data Storage

LocalStorage may be used to preserve user preferences and local application data, including:

- Selected theme.
- Interface language.
- Translation language and visibility.
- Bookmarked verses.
- Last reading position.
- Digital Tasbih counter.

These settings are stored in the user's browser and may not automatically transfer to another browser or device. Clearing browser data can remove locally saved information.

---

## 🔐 Privacy

Quran Al-Kareem is designed as a browser-based reading experience. Local preferences can be stored in the browser using LocalStorage.

Online Quran data, fonts, or audio may be requested from external services. Their availability and privacy practices are governed by the respective providers. Avoid storing sensitive personal information in browser storage.

---

## 🧪 Testing Checklist

Before publishing the project, verify the following:

- [ ] All 114 Surahs can be selected.
- [ ] Arabic Quranic verses load correctly.
- [ ] Bangla mode displays genuine Bangla translations.
- [ ] English mode displays the selected English translation.
- [ ] The top translation button shows and hides translations.
- [ ] Translation preferences persist after refreshing.
- [ ] Dark and light themes work correctly.
- [ ] Bookmarks can be saved, removed, and reopened.
- [ ] Audio controls handle unavailable audio gracefully.
- [ ] Search and verse navigation work correctly.
- [ ] Tasbih counting, undo, and reset work as expected.
- [ ] The website works on desktop and mobile screens.
- [ ] All referenced local files exist.
- [ ] Network errors display helpful messages.

---

## 🐛 Troubleshooting

**Quran data is not loading**

- Check your internet connection.
- Confirm that the API service is available.
- Refresh the page and try again.
- Check the browser console for errors.

**Bangla translation is missing**

- Verify that the selected translation edition is supported by the API.
- Check whether the translation request succeeded.
- Do not substitute English text under a Bangla translation label.

**Audio is not playing**

- Check your internet connection.
- Verify that the selected recitation has a valid audio URL.
- Check your browser's audio permissions and volume settings.

**Changes are not being saved**

- Confirm that browser storage is enabled.
- Avoid clearing site data if you want to preserve bookmarks and settings.
- Remember that LocalStorage is specific to the browser and origin.

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome.

1. Fork the repository.
2. Create a new branch for your changes.
3. Make your changes and test them.
4. Commit your work with a clear message.
5. Submit a pull request describing your improvements.

Please take special care when modifying Quranic text, translations, Arabic pronunciation, or religious content. Verify such changes using reliable sources.

---

## 📜 License

No specific license is declared here. Add a `LICENSE` file before distributing the project publicly, and ensure that any external fonts, images, audio, and translation data are used according to their respective licenses and terms.

---

## 🌟 Project Goal

The goal of **Quran Al-Kareem** is to provide a peaceful, accessible, and convenient digital space where people can read the Holy Quran, understand its meaning, listen to available recitations, save meaningful verses, and maintain their daily Dhikr.

May this project encourage reflection, understanding, and a closer connection with the Holy Quran.

**القرآن الكريم — Read. Reflect. Remember.**

