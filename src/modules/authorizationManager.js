const fs = require('fs');
const path = require('path');

const CONFIG_PATH = path.join(__dirname, '../config/authorizedUsers.json');

class AuthorizationManager {
  constructor() {
    this.authorizedUsers = [];
    this.isProductionMode = false;
    this.load();
  }

  load() {
    try {
      if (!fs.existsSync(CONFIG_PATH)) {
        console.warn('[Authorization] ⚠️  authorizedUsers.json not found — running in development mode (all users allowed)');
        this.authorizedUsers = [];
        this.isProductionMode = false;
        return;
      }

      const raw = fs.readFileSync(CONFIG_PATH, 'utf-8');
      const data = JSON.parse(raw);
      this.authorizedUsers = data.authorizedUsers || [];

      if (this.authorizedUsers.length === 0) {
        console.warn('[Authorization] ⚠️  authorizedUsers.json is empty — running in development mode (all users allowed)');
        this.isProductionMode = false;
      } else {
        console.log(`[Authorization] ✅ Loaded ${this.authorizedUsers.length} authorized user(s) — production mode active`);
        this.isProductionMode = true;
      }
    } catch (error) {
      console.error('[Authorization] ❌ Failed to load authorizedUsers.json:', error.message);
      console.warn('[Authorization] ⚠️  Falling back to development mode (all users allowed)');
      this.authorizedUsers = [];
      this.isProductionMode = false;
    }
  }

  save() {
    try {
      fs.writeFileSync(CONFIG_PATH, JSON.stringify({ authorizedUsers: this.authorizedUsers }, null, 2), 'utf-8');
    } catch (error) {
      console.error('[Authorization] ❌ Failed to save authorizedUsers.json:', error.message);
    }
  }

  isAuthorized(userId) {
    if (!this.isProductionMode) {
      return true;
    }
    return this.authorizedUsers.includes(userId);
  }

  addAuthorizedUser(userId) {
    if (!this.authorizedUsers.includes(userId)) {
      this.authorizedUsers.push(userId);
      this.save();
      console.log(`[Authorization] ✅ User ${userId} authorized`);
    }
    return this.authorizedUsers.includes(userId);
  }

  removeAuthorizedUser(userId) {
    const index = this.authorizedUsers.indexOf(userId);
    if (index !== -1) {
      this.authorizedUsers.splice(index, 1);
      this.save();
      console.log(`[Authorization] 🗑️ User ${userId} removed from allowlist`);
    }
    return !this.authorizedUsers.includes(userId);
  }
}

module.exports = new AuthorizationManager();
