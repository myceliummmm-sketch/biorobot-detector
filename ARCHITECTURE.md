# 🍄 Mycelium OS: Sovereign Architecture (v1.1 - Use Cases v3 Aligned)

## 🌍 Global Vision
Mycelium OS is a hybrid workspace where **Telegram (CUI)** meets **Web Canvas (GUI)**.
- **Single Source of Truth:** Supabase.
- **Flow:** Onboarding -> Idea (5 Cards) -> Research (5 Cards) -> Build (5 Cards).
- **Core Principle:** "Evaluate -> Forge -> Earn".

---

## 🏗 The 3 Pillars

### 1. The Brain (Supabase)
*Central Storage & Logic.*
* **Database:**
    * `profiles`: User identity, `spores_balance` (Economy), `xp` (Gamification).
    * `projects`: Workspaces, `current_phase` (Idea/Research/Build), `health_score`.
    * `cards`: Stores `content` (JSON), `rarity` (Common/Epic/Legendary), `score` (0-100), `type` (text slug).
    * `transactions`: Log of Spores earned/spent.
* **Edge Functions:**
    * `voice-extractor`: Transcribes audio -> Structured JSON.
    * `evaluate-card`: **CRITICAL.** Analyzes input -> Assigns Score & Rarity -> Calculates Spore Reward.
    * `forge-artifact`: Generates visual assets.

### 2. The Swarm (Python/Aiogram 3)
*Interface: Telegram. Hosting: Railway.*
* **Structure:** Single Process, Multi-Bot Dispatcher.
* **Agents:**
    * **@PrismaBot (The PM):** Guide. Active in `#Idea`. Handles logic for "I don't know" (Auto-fill cost: 10 Spores).
    * **@ToxicBot (The Critic):** Validator. Checks for bullshit.
* **Key Commands:**
    * `/start` - Onboarding & Mode Selection (Pet/Startup/Life).
    * `/balance` - Show Spores & Earning rules (UC-50).

### 3. The Face (React/Vite)
*Interface: Telegram Mini App (TMA).*
* **Role:** Visual editing, "Forge" animation (Confetti for Epic/Legendary), Marketplace.
* **Sync:** Real-time subscriptions to Supabase.

---

## 🔄 The "Voice-to-Value" Pipeline (Updated v3)

1.  **Input:** User sends Voice/Text to `#Idea`.
2.  **Draft:** System extracts data -> saves as `draft`.
3.  **Evaluation (The Judge):**
    * System runs `evaluate-card`.
    * Determines **Rarity** (Common/Rare/Epic/Legendary).
4.  **Feedback:** Prisma says: "Captured. This looks like a LEGENDARY insight (+25 spores). Commit?"
5.  **Forge (Commit):**
    * User approves.
    * Card status -> `done`.
    * **Spores Credited** to User (+10/25/100).
    * **Artifact Generated** in WebApp.

---

## 💰 Economy Rules (v3 Implementation)
* **Costs:**
    * Reforge (Fixing a bad card): **-10 Spores**.
    * Auto-fill ("I don't know" button): **-10 Spores**.
* **Rewards:**
    * Epic Card: **+10 Spores**.
    * Legendary Card: **+25 Spores**.
    * Phase Completion (Idea): **+20 Spores**.

## 🛠 Tech Constraints
* **Database:** Use `text` for `card_type` to support all 15 cards (Idea/Research/Build) without constant enum migrations.
* **Validation:** Bots must check `spores_balance` BEFORE executing expensive actions (Auto-fill).
