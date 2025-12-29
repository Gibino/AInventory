/**
 * Emoji data for the category emoji picker
 * Organized by category with commonly used food, household, and object emojis
 */
const EMOJI_DATA = {
    "frequently_used": {
        label: { "pt-BR": "Usados Recentemente", "en-US": "Recently Used" },
        emojis: [] // Will be populated from localStorage
    },
    "food_drink": {
        label: { "pt-BR": "Alimentos & Bebidas", "en-US": "Food & Drink" },
        emojis: [
            "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🫐", "🍈",
            "🍒", "🍑", "🥭", "🍍", "🥥", "🥝", "🍅", "🍆", "🥑", "🥦",
            "🥬", "🥒", "🌶️", "🫑", "🌽", "🥕", "🫒", "🧄", "🧅", "🥔",
            "🍠", "🥐", "🥯", "🍞", "🥖", "🥨", "🧀", "🥚", "🍳", "🧈",
            "🥞", "🧇", "🥓", "🥩", "🍗", "🍖", "🦴", "🌭", "🍔", "🍟",
            "🍕", "🫓", "🥪", "🥙", "🧆", "🌮", "🌯", "🫔", "🥗", "🥘",
            "🫕", "🍝", "🍜", "🍲", "🍛", "🍣", "🍱", "🥟", "🦪", "🍤",
            "🍙", "🍚", "🍘", "🍥", "🥠", "🥮", "🍢", "🍡", "🍧", "🍨",
            "🍦", "🥧", "🧁", "🍰", "🎂", "🍮", "🍭", "🍬", "🍫", "🍿",
            "🍩", "🍪", "🌰", "🥜", "🫘", "🍯", "🥛", "🍼", "☕", "🫖",
            "🍵", "🧃", "🥤", "🧋", "🍶", "🍺", "🍻", "🥂", "🍷", "🥃",
            "🍸", "🍹", "🧉", "🍾", "🧊"
        ]
    },
    "household": {
        label: { "pt-BR": "Casa & Limpeza", "en-US": "Household & Cleaning" },
        emojis: [
            "🧹", "🧺", "🧻", "🪣", "🧽", "🪥", "🧴", "🧼", "🪒", "🧷",
            "🧯", "🛁", "🚿", "🪠", "🛋️", "🪑", "🚪", "🛏️", "🪟", "🧲",
            "🔧", "🔨", "🪛", "🔩", "⚙️", "🗜️", "🔌", "💡", "🔦", "🕯️",
            "🪔", "🛢️", "💎", "📦", "🗑️", "🧰", "🪜", "🧳", "🎁"
        ]
    },
    "personal_care": {
        label: { "pt-BR": "Higiene & Beleza", "en-US": "Personal Care" },
        emojis: [
            "🧴", "🧷", "🧹", "🧺", "🧻", "🧼", "🧽", "🧾", "🪒", "🪥",
            "💄", "💅", "💆", "💇", "🧖", "🩹", "🩺", "💊", "💉", "🩸",
            "🧬", "🧪", "🔬", "👓", "🕶️", "🥽", "👔", "👕", "👖", "🧣",
            "🧤", "🧥", "🧦", "👗", "👘", "🥻", "🩱", "🩲", "🩳", "👙"
        ]
    },
    "pets": {
        label: { "pt-BR": "Pets", "en-US": "Pets" },
        emojis: [
            "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯",
            "🦁", "🐮", "🐷", "🐽", "🐸", "🐵", "🙈", "🙉", "🙊", "🐒",
            "🐔", "🐧", "🐦", "🐤", "🐣", "🐥", "🦆", "🦅", "🦉", "🦇",
            "🐺", "🐗", "🐴", "🦄", "🐝", "🪱", "🐛", "🦋", "🐌", "🐞",
            "🐜", "🪰", "🪲", "🪳", "🦗", "🦂", "🐢", "🐍", "🦎", "🦖",
            "🦕", "🐙", "🦑", "🦐", "🦞", "🦀", "🐡", "🐠", "🐟", "🐬",
            "🐳", "🐋", "🦈", "🐊", "🐅", "🐆", "🦓", "🦍", "🦧", "🦣"
        ]
    },
    "objects": {
        label: { "pt-BR": "Objetos", "en-US": "Objects" },
        emojis: [
            "⌚", "📱", "💻", "⌨️", "🖥️", "🖨️", "🖱️", "🖲️", "🕹️", "🗜️",
            "💽", "💾", "💿", "📀", "📼", "📷", "📸", "📹", "🎥", "📽️",
            "🎞️", "📞", "☎️", "📟", "📠", "📺", "📻", "🎙️", "🎚️", "🎛️",
            "🧭", "⏱️", "⏲️", "⏰", "🕰️", "⌛", "⏳", "📡", "🔋", "🪫",
            "🔌", "💡", "🔦", "🕯️", "🪔", "🧯", "🛢️", "💸", "💵", "💴",
            "💶", "💷", "🪙", "💰", "💳", "💎", "⚖️", "🪜", "🧰", "🪛"
        ]
    },
    "symbols": {
        label: { "pt-BR": "Símbolos", "en-US": "Symbols" },
        emojis: [
            "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
            "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "✨", "⭐",
            "🌟", "💫", "🔥", "💥", "⚡", "🌈", "☀️", "🌤️", "⛅", "🌦️",
            "✅", "❌", "⚠️", "📌", "📍", "🏷️", "🔖", "📁", "📂", "🗂️"
        ]
    }
};

// Load frequently used emojis from localStorage
function loadFrequentlyUsed() {
    try {
        const stored = localStorage.getItem('emoji-frequently-used');
        if (stored) {
            EMOJI_DATA.frequently_used.emojis = JSON.parse(stored).slice(0, 16);
        }
    } catch (e) {
        console.error('Error loading frequently used emojis:', e);
    }
}

// Save emoji to frequently used
function addToFrequentlyUsed(emoji) {
    try {
        let frequent = EMOJI_DATA.frequently_used.emojis || [];
        // Remove if already exists
        frequent = frequent.filter(e => e !== emoji);
        // Add to front
        frequent.unshift(emoji);
        // Keep only 16
        frequent = frequent.slice(0, 16);
        EMOJI_DATA.frequently_used.emojis = frequent;
        localStorage.setItem('emoji-frequently-used', JSON.stringify(frequent));
    } catch (e) {
        console.error('Error saving frequently used emoji:', e);
    }
}

// Search emojis across all categories
function searchEmojis(query) {
    if (!query) return null;
    const results = [];
    const lowerQuery = query.toLowerCase();

    // Simple search - in a real app you'd have emoji names/keywords
    // For now, just return all emojis that match food/drink if query relates to food
    // This is a simplified version
    Object.values(EMOJI_DATA).forEach(category => {
        if (category.emojis) {
            results.push(...category.emojis);
        }
    });

    return results.slice(0, 50); // Return first 50 matches
}

// Initialize on load
loadFrequentlyUsed();
