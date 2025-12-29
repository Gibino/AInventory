# 🏠 AInventory / AInventário

Smart home inventory management designed for simplicity, visual feedback, and efficiency. Built with accessibility in mind for neurodivergent users (ADHD/ASD) with clean design and immediate feedback.

## ✨ Features

### Core Functionality
- **📊 Visual Dashboard**: Real-time status of items (OK, Low, Empty) with color-coded indicators
- **🛒 Automatic Shopping List**: Items below minimum quantity go straight to the list with suggested purchase quantities
- **➕/➖ Quick Actions**: Large, accessible buttons for easy daily tracking
- **📱 Mobile-First Design**: Responsive layout that works great on phone, tablet, and desktop

### AI & Smart Features
- **📷 AI Product Scanner**: Point your camera at any product - Gemini AI identifies it automatically and suggests category, name, and unit
- **🧠 ML Predictions**: Linear regression model learns your usage patterns to predict when items will run out
- **📲 SMS Low-Stock Notifications**: Automatic alerts when stock drops below minimum (via Textbelt)
- **💡 Smart Purchase Suggestions**: Calculated recommended quantities based on:
  - Current usage rate
  - Acquisition difficulty (Easy/Medium/Hard → 3/7/14 day buffers)
  - Target: 150% of minimum for safety margin

### Customization & Personalization
- **🌙 Dark / ☀️ Light / 📱 System Themes**: Segmented theme switcher with instant apply
- **🇧🇷 Português / 🇺🇸 English**: Full localization support with immediate language switching
- **🎨 Raycast-Style Emoji Picker**: Visual category icons with searchable emoji picker and frequently used tracking
- **🔐 User Authentication**: Secure JWT-based login with profile management

### Inventory Management
- **� Category Organization**: Group items by custom categories with emoji icons
- **⚖️ Flexible Units**: Support for various units (un, kg, g, L, ml, packets)
- **📝 Notes & Barcodes**: Add notes and barcode info to items
- **📈 Usage Tracking**: Track consumption patterns over time

## �🚀 Getting Started

### Option 1: Docker (Recommended)

```bash
docker-compose up --build
```

Open: `http://localhost:8001`

### Option 2: Local Python

1. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate   # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Run the server:
   ```bash
   python -m backend.main
   ```

Open: `http://localhost:8000`

## ⚙️ Configuration (.env)

```env
# JWT Secret (generate a random string for production)
SECRET_KEY=your-super-secret-key-here

# Google Gemini AI (for product scanning)
# Get your key at: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-gemini-api-key

# SMS Notifications via Textbelt (optional)
# Free tier: 1 SMS per day
# Paid tier: Get a key at https://textbelt.com
TEXTBELT_KEY=textbelt
```

---

## 📱 SMS Notifications Walkthrough

AInventory sends SMS alerts when items run low, with smart suggestions on how much to buy.

### How It Works

1. When you decrement an item **below its minimum quantity**, the system:
   - Calculates a **Suggested Purchase Quantity** based on:
     - Your usage rate (if configured)
     - Acquisition difficulty (Easy/Medium/Hard items get 3/7/14 day buffers)
     - Target: 150% of minimum for safety margin
   - Sends an SMS to your phone number

2. **Rate limiting**: Only 1 SMS per item per 24 hours (prevents spam)

### Setup Steps

1. **Set your phone number** in your user profile:
   - Click ⚙️ Settings → Edit Profile
   - Enter your phone with country code: `+5511999999999`

2. **Configure Textbelt** (optional - works out of the box):
   - Free tier: 1 SMS/day (default key: `textbelt`)
   - For more SMS: Buy a key at [textbelt.com](https://textbelt.com) (~$0.01/SMS)
   - Add to `.env`: `TEXTBELT_KEY=your-paid-key`

3. **Test it**:
   - Find an item near its minimum quantity
   - Click the **−** button to drop it below minimum
   - You should receive an SMS like:
   ```
   ⚠️ AInventário: Arroz está acabando!
   Atual: 0.5 kg
   Mínimo: 1 kg
   Sugestão de compra: 2.5 kg
   ```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| No SMS received | Check phone number format (include `+` and country code) |
| "Quota exceeded" | Free tier allows 1 SMS/day. Wait 24h or get paid key |
| Wrong language | SMS language matches your app language preference |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.11+) |
| **Database** | SQLite |
| **Frontend** | Vanilla HTML/CSS/JS |
| **AI** | Google Gemini 2.5 Flash |
| **ML** | scikit-learn (Linear Regression) |
| **SMS** | Textbelt API |
| **Auth** | JWT (python-jose + bcrypt) |
| **Container** | Docker |

## 🗺️ Roadmap

- [ ] Multi-user / Family sharing
- [ ] Weekly usage reports & dashboards
- [ ] WhatsApp notifications