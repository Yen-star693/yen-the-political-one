"""
Yen: an absurd, overengineered Discord government bot.

Commands (all messages, no slash commands, prefix "yen "):

    yen declare a new martial law
    yen laws
    yen grant @user permission to <permission action from an active law>
    yen revoke the law <EXACT LAW ID>
    yen button

See laws.py for how the law system is structured and gov_text.py for the
bureaucratic flavor text pools.
"""

import asyncio
import os
import time

import discord
from dotenv import load_dotenv

import gov_text
import laws
import storage

load_dotenv()

ROLE_NAME = "Supreme Minister of 67"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)


# ---------------------------------------------------------------------------
# Role / authority helpers
# ---------------------------------------------------------------------------

async def ensure_supreme_minister_role(guild):
    """Create the Supreme Minister of 67 role if it does not already exist.

    The role intentionally carries no Discord permissions of its own; it is
    purely a marker the bot checks for command authority.
    """
    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if role is None:
        try:
            role = await guild.create_role(
                name=ROLE_NAME,
                colour=discord.Colour.gold(),
                permissions=discord.Permissions.none(),
                mentionable=True,
                reason="Yen government initialization",
            )
        except discord.Forbidden:
            return None
    guild_state = storage.get_guild_state(guild.id)
    guild_state["role_id"] = role.id
    storage.save()
    return role


def get_supreme_minister(guild):
    """Return the Member currently holding the role, or None."""
    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if role is None or not role.members:
        return None
    return role.members[0]


def is_supreme_minister(member, guild):
    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if role is None:
        return False
    return role in member.roles


# ---------------------------------------------------------------------------
# Government Compliance button
# ---------------------------------------------------------------------------

class ComplianceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Government Compliance",
        style=discord.ButtonStyle.primary,
        custom_id="yen_gov_compliance_button",
    )
    async def comply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(gov_text.COMPLIANCE_STAGES[0])
        for stage in gov_text.COMPLIANCE_STAGES[1:]:
            await asyncio.sleep(1)
            try:
                await interaction.edit_original_response(content=stage)
            except discord.HTTPException:
                return
        await asyncio.sleep(1)
        try:
            await interaction.edit_original_response(
                content=gov_text.compliance_approved_line()
            )
        except discord.HTTPException:
            pass


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def handle_declare(message):
    guild_state = storage.get_guild_state(message.guild.id)
    active_ids = set(guild_state["laws"].keys())
    available_types = [
        type_key for type_key, entry in laws.LAW_TYPES.items()
        if entry["make"]().get("id") not in active_ids
    ] if False else None  # placeholder, replaced below for clarity

    # Prefer a law type whose id is not currently active. If every type is
    # already active, just refresh a random one instead of doing nothing.
    inactive_type_keys = [t for t in laws.LAW_TYPES if t not in active_ids]
    pool = inactive_type_keys if inactive_type_keys else list(laws.LAW_TYPES.keys())
    type_key = __import__("random").choice(pool)

    law_data = laws.LAW_TYPES[type_key]["make"]()
    law_id = law_data["id"]

    guild_state["laws"][law_id] = {
        "type": type_key,
        "description": law_data["description"],
        "params": law_data["params"],
        "violation_text": law_data["violation_text"],
        "permission_action": law_data["permission_action"],
        "created_at": time.time(),
    }
    guild_state["exemptions"].setdefault(law_id, [])
    storage.save()

    text = (
        "{intro}\n\n"
        "{law_id}\n"
        "{description}\n\n"
        "Please contact @{role} and ask them to use:\n"
        "yen grant @someone permission to {permission}\n\n"
        "The Supreme Minister of 67 must use the exact command shown above."
    ).format(
        intro=gov_text.declare_intro(),
        law_id=law_id,
        description=law_data["description"],
        role=ROLE_NAME,
        permission=law_data["permission_action"],
    )

    await message.channel.send(
        "@everyone {}".format(text),
        allowed_mentions=discord.AllowedMentions(everyone=True),
    )


async def handle_laws(message):
    guild_state = storage.get_guild_state(message.guild.id)
    active_laws = guild_state["laws"]

    if not active_laws:
        await message.channel.send(
            "Yen Laws\n\nNo laws are currently active. The nation is, "
            "regrettably, at peace."
        )
        return

    blocks = ["Yen Laws"]
    for law_id, law in active_laws.items():
        blocks.append(
            "\n{law_id}\n{description}\n"
            "To revoke this law, the Supreme Minister of 67 must say exactly:\n"
            "yen revoke the law {law_id}".format(
                law_id=law_id, description=law["description"]
            )
        )
    await message.channel.send("\n".join(blocks))


async def handle_button(message):
    await message.channel.send(
        "The government has prepared an official compliance procedure.",
        view=ComplianceView(),
    )


async def handle_grant(message, body_after_yen):
    guild = message.guild
    guild_state = storage.get_guild_state(guild.id)

    if not is_supreme_minister(message.author, guild):
        await message.channel.send(
            "{opener} Only the {role} may issue government exemptions.".format(
                opener=gov_text.rejection_opener(), role=ROLE_NAME
            )
        )
        return

    if not message.mentions:
        await message.channel.send(
            "{opener} No user was mentioned. The exact required format is:\n"
            "yen grant @someone permission to <the exact permission text "
            "shown in the law announcement>".format(opener=gov_text.rejection_opener())
        )
        return

    target = message.mentions[0]

    remainder = body_after_yen[len("grant "):]
    lower_remainder = remainder.lower()
    marker = "permission to "
    idx = lower_remainder.find(marker)
    if idx == -1:
        await message.channel.send(
            "{opener} That command is not formatted correctly. The exact "
            "required format is:\n"
            "yen grant @someone permission to <the exact permission text "
            "shown in the law announcement>".format(opener=gov_text.rejection_opener())
        )
        return

    phrase = remainder[idx + len(marker):].strip().rstrip(".")

    matched_law_id = None
    for law_id, law in guild_state["laws"].items():
        if law.get("permission_action", "").lower() == phrase.lower():
            matched_law_id = law_id
            break

    if matched_law_id is None:
        await message.channel.send(
            "{opener} No active law currently requires that permission. "
            "Check `yen laws` for the exact wording required.".format(
                opener=gov_text.rejection_opener()
            )
        )
        return

    exemptions = guild_state["exemptions"].setdefault(matched_law_id, [])
    if target.id in exemptions:
        await message.channel.send(
            "{} already holds an exemption from {}.".format(
                target.mention, matched_law_id
            )
        )
        return

    exemptions.append(target.id)
    storage.save()

    await message.channel.send(
        "{opener} {user} is now exempt from the law {law_id} and may "
        "{permission}.".format(
            opener=gov_text.grant_success_opener(),
            user=target.mention,
            law_id=matched_law_id,
            permission=guild_state["laws"][matched_law_id]["permission_action"],
        )
    )


async def handle_revoke(message, candidate_id):
    guild = message.guild
    guild_state = storage.get_guild_state(guild.id)

    if not is_supreme_minister(message.author, guild):
        await message.channel.send(
            "{opener} Only the {role} may revoke laws.".format(
                opener=gov_text.rejection_opener(), role=ROLE_NAME
            )
        )
        return

    if candidate_id in guild_state["laws"]:
        del guild_state["laws"][candidate_id]
        guild_state["exemptions"].pop(candidate_id, None)
        storage.save()
        await message.channel.send(
            "{opener} {law_id} is no longer enforced. All associated "
            "exemptions have been cleared.".format(
                opener=gov_text.revoke_success_opener(), law_id=candidate_id
            )
        )
        return

    close_match = discord.utils.find(
        lambda existing: existing.lower() == candidate_id.lower(),
        guild_state["laws"].keys(),
    )
    if close_match:
        await message.channel.send(
            "{opener} No active law exactly matches \"{candidate}\". The "
            "law identifier must be copied exactly, including "
            "capitalization, from `yen laws`. Did you mean: "
            "yen revoke the law {actual}".format(
                opener=gov_text.rejection_opener(),
                candidate=candidate_id,
                actual=close_match,
            )
        )
        return

    await message.channel.send(
        "{opener} No active law matches \"{candidate}\". Use `yen laws` "
        "to see the exact identifiers currently in effect.".format(
            opener=gov_text.rejection_opener(), candidate=candidate_id
        )
    )


async def handle_command(message, body):
    body_stripped = body.strip()
    lower_body = body_stripped.lower()

    if lower_body == "declare a new martial law":
        await handle_declare(message)
    elif lower_body == "laws":
        await handle_laws(message)
    elif lower_body == "button":
        await handle_button(message)
    elif lower_body.startswith("grant "):
        await handle_grant(message, body_stripped)
    elif lower_body.startswith("revoke the law "):
        prefix_len = len("revoke the law ")
        candidate_id = body_stripped[prefix_len:].strip()
        if not candidate_id:
            await message.channel.send(
                "{opener} No law identifier was provided. Use `yen laws` "
                "to see the exact identifiers currently in effect.".format(
                    opener=gov_text.rejection_opener()
                )
            )
            return
        await handle_revoke(message, candidate_id)
    # Unrecognized "yen ..." messages are silently ignored so the bot does
    # not spam the channel every time someone happens to type "yen" in
    # normal conversation.


# ---------------------------------------------------------------------------
# Law enforcement
# ---------------------------------------------------------------------------

async def enforce_laws(message):
    guild_state = storage.get_guild_state(message.guild.id)
    active_laws = guild_state["laws"]
    if not active_laws:
        return

    now = time.time()
    last_ts_map = guild_state.setdefault("last_message_ts", {})
    user_key = str(message.author.id)
    last_ts = last_ts_map.get(user_key)

    violations = []
    for law_id, law in active_laws.items():
        exemptions = guild_state["exemptions"].get(law_id, [])
        if message.author.id in exemptions:
            continue

        if law["type"] == "MESSAGE LIMIT":
            seconds = law["params"]["seconds"]
            if last_ts is not None and (now - last_ts) < seconds:
                violations.append((law_id, law))
            continue

        checker = laws.LAW_TYPES.get(law["type"], {}).get("check")
        if checker is None:
            continue
        if checker(message.content, law["params"]):
            violations.append((law_id, law))

    last_ts_map[user_key] = now
    storage.save()

    if not violations:
        return

    try:
        await message.delete()
    except (discord.Forbidden, discord.NotFound, discord.HTTPException):
        pass

    lines = [gov_text.violation_header()]
    for law_id, law in violations:
        lines.append(
            "{mention} has violated the active law: {law_id}.\n{detail}".format(
                mention=message.author.mention,
                law_id=law_id,
                detail=law["violation_text"],
            )
        )

    try:
        await message.channel.send("\n\n".join(lines))
    except discord.HTTPException:
        pass


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@client.event
async def on_ready():
    client.add_view(ComplianceView())
    for guild in client.guilds:
        try:
            await ensure_supreme_minister_role(guild)
        except discord.HTTPException:
            continue
    print("Yen is online as {}".format(client.user))


@client.event
async def on_guild_join(guild):
    try:
        await ensure_supreme_minister_role(guild)
    except discord.HTTPException:
        pass


@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.guild is None:
        return

    content = message.content or ""
    if content.strip().lower().startswith("yen "):
        try:
            await handle_command(message, content.strip()[4:])
        except discord.HTTPException:
            pass
        return

    try:
        await enforce_laws(message)
    except discord.HTTPException:
        pass


def main():
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "DISCORD_BOT_TOKEN environment variable is not set. Set it in "
            "your .env file locally or in the Render dashboard."
        )

    from keep_alive import keep_alive
    keep_alive()

    client.run(token)


if __name__ == "__main__":
    main()
