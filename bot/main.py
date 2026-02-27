from __future__ import annotations

import os
from dataclasses import dataclass

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from quiz_manager import QuizManager


@dataclass
class Config:
    token: str
    questions_file: str
    prefix: str


def load_config() -> Config:
    load_dotenv()

    token = os.getenv("DISCORD_TOKEN", "")
    questions_file = os.getenv("QUIZ_QUESTIONS_FILE", "data/questions.json")
    prefix = os.getenv("COMMAND_PREFIX", "!")

    if not token:
        raise RuntimeError("DISCORD_TOKEN tanımlı değil. .env dosyasını kontrol et.")

    return Config(token=token, questions_file=questions_file, prefix=prefix)


config = load_config()
quiz = QuizManager(config.questions_file)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=config.prefix, intents=intents)
active_questions: dict[int, int] = {}


class AnswerSelect(discord.ui.Select):
    def __init__(self, user_id: int, question_index: int, choices: list[str]):
        options = [
            discord.SelectOption(label=f"{i + 1}. {choice[:90]}", value=str(i))
            for i, choice in enumerate(choices)
        ]
        super().__init__(placeholder="Cevabını seç", min_values=1, max_values=1, options=options)
        self.user_id = user_id
        self.question_index = question_index

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Bu soru sana ait değil. /quiz-start ile kendi oyununu başlat.", ephemeral=True
            )
            return

        selected_index = int(self.values[0])
        is_correct, message = quiz.check_answer(self.user_id, self.question_index, selected_index)
        score = quiz.current_score(self.user_id)

        followup = f"{message}\nAnlık skorun: **{score}**"
        if not is_correct:
            followup += "\nDevam etmek için /quiz-next kullanabilirsin."

        active_questions.pop(self.user_id, None)
        await interaction.response.send_message(followup, ephemeral=True)


class AnswerView(discord.ui.View):
    def __init__(self, user_id: int, question_index: int, choices: list[str]):
        super().__init__(timeout=90)
        self.add_item(AnswerSelect(user_id, question_index, choices))


@bot.event
async def on_ready() -> None:
    synced = await bot.tree.sync()
    print(f"{bot.user} giriş yaptı. {len(synced)} slash komutu senkronlandı.")


@bot.tree.command(name="quiz-start", description="Bilgi yarışmasını başlatır.")
async def quiz_start(interaction: discord.Interaction) -> None:
    quiz.start_session(interaction.user.id)
    active_questions.pop(interaction.user.id, None)
    await interaction.response.send_message(
        "Quiz başladı! İlk soru için /quiz-next yaz.", ephemeral=True
    )


@bot.tree.command(name="quiz-next", description="Sıradaki soruyu gönderir.")
async def quiz_next(interaction: discord.Interaction) -> None:
    user_id = interaction.user.id
    if not quiz.has_session(user_id):
        await interaction.response.send_message(
            "Önce /quiz-start ile oyunu başlat.", ephemeral=True
        )
        return

    if user_id in active_questions:
        await interaction.response.send_message(
            "Önce mevcut sorunu cevapla.", ephemeral=True
        )
        return

    payload = quiz.next_question(user_id)
    if payload is None:
        score = quiz.stop_session(user_id)
        await interaction.response.send_message(
            f"Sorular bitti! Final skorun: **{score}**. Tekrar oynamak için /quiz-start kullan.",
            ephemeral=True,
        )
        return

    question_index, question = payload
    active_questions[user_id] = question_index

    choice_lines = "\n".join(f"**{i + 1}.** {c}" for i, c in enumerate(question.choices))
    content = f"**Soru:** {question.question}\n\n{choice_lines}"

    await interaction.response.send_message(
        content,
        view=AnswerView(user_id, question_index, question.choices),
        ephemeral=True,
    )


@bot.tree.command(name="quiz-score", description="Mevcut skorunu gösterir.")
async def quiz_score(interaction: discord.Interaction) -> None:
    score = quiz.current_score(interaction.user.id)
    await interaction.response.send_message(f"Skorun: **{score}**", ephemeral=True)


@bot.tree.command(name="quiz-stop", description="Quiz oturumunu sonlandırır.")
async def quiz_stop(interaction: discord.Interaction) -> None:
    score = quiz.stop_session(interaction.user.id)
    active_questions.pop(interaction.user.id, None)
    await interaction.response.send_message(
        f"Oyun sonlandırıldı. Toplam skorun: **{score}**", ephemeral=True
    )


if __name__ == "__main__":
    bot.run(config.token)
