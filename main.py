
import discord
import config as f
import json
from typing import Union
import logging
import textwrap

import asyncio
import random
import datetime
import DiscordUtils

from discord.ext import commands
Intents = discord.Intents.default()
Intents.members = True
Intents.presences = True

bot = commands.Bot(command_prefix=f.prefix,Intents=Intents)





class Help(commands.HelpCommand):
    def __init__(self):
        super().__init__()
        self.no_category = "カテゴリ未設定"
        self.command_attrs["description"] = "このメッセージを表示します。"
        self.command_attrs["help"] = "このBOTのヘルプコマンドです。"

    async def create_category_tree(self, category, enclosure):
        """
        コマンドの集まり（Group、Cog）から木の枝状のコマンドリスト文字列を生成する。
        生成した文字列は enlosure 引数に渡された文字列で囲われる。
        """
        content = ""
        command_list = category.walk_commands()
        for cmd in await self.filter_commands(command_list, sort=True):
            if cmd.root_parent:
                # cmd.root_parent は「根」なので、根からの距離に応じてインデントを増やす
                index = cmd.parents.index(cmd.root_parent)
                indent = "\t" * (index + 1)
                if indent:
                    content += f"{indent}- {cmd.name} / {cmd.description}\n"
                else:
                    # インデントが入らない、つまり木の中で最も浅く表示されるのでprefixを付加
                    content += f"{self.context.prefix}{cmd.name} / {cmd.description}\n"
            else:
                # 親を持たないコマンドなので、木の中で最も浅く表示する。prefixを付加
                content += f"{self.context.prefix}{cmd.name} / {cmd.description}\n"

        return enclosure + textwrap.dedent(content) + enclosure

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="helpコマンド", color=0x5d00ff)
        if self.context.bot.description:
            # もしBOTに description 属性が定義されているなら、それも埋め込みに追加する
            embed.description = self.context.bot.description
            embed.add_field(name="サポート", value="https://discord.gg/uPbXyFh6")
        for cog in mapping:
            if cog:
                cog_name = cog.qualified_name
            else:
                # mappingのキーはNoneになる可能性もある
                # もしキーがNoneなら、自身のno_category属性を参照する
                cog_name = self.no_category

            command_list = await self.filter_commands(mapping[cog], sort=True)
            content = ""
            for cmd in command_list:
                content += f"`{cmd.name}` "
            embed.add_field(name=cog_name, value=content, inline=False)

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title=cog.quaylified_name, description=cog.description, color=0x00ff00)
        embed.add_field(name="コマンドリスト：", value=await self.create_category_tree(cog, "```"))
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=f"{self.context.prefix}{group.qualified_name}",
                              description=group.description, color=0x00ff00)
        if group.aliases:
            embed.add_field(name="有効なエイリアス：", value="`" + "`, `".join(group.aliases) + "`", inline=True)
        if group.help:
            embed.add_field(name="必要な権限：", value=group.help, inline=True)
        embed.add_field(name="サブコマンドリスト：", value=await self.create_category_tree(group, "```"), inline=True)
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        params = " ".join(command.clean_params.keys())
        embed = discord.Embed(title=f"{self.context.prefix}{command.qualified_name} {params}",
                              description=command.description, color=0x00ff00)
        if command.aliases:
            embed.add_field(name="有効なエイリアス：", value="`" + "`, `".join(command.aliases) + "`", inline=True)
        if command.help:
            embed.add_field(name="必要な権限：", value=command.help, inline=True)
        if command.name:
            embed.add_field(name="name", value=command.name, inline=True)

        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        embed = discord.Embed(title="ヘルプ表示のエラー", description=error, color=0xff0000)
        await self.get_destination().send(embed=embed)

    def command_not_found(self, string):
        return f"{string} というコマンドは存在しません。"

    def subcommand_not_found(self, command, string):
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            # もし、そのコマンドにサブコマンドが存在しているなら
            return f"{command.qualified_name} に {string} というサブコマンドは登録されていません。"
        return f"{command.qualified_name} にサブコマンドは登録されていません。"


bot = commands.Bot(command_prefix="y/", help_command=Help(), description="```y/helps で調べられます``` ")

developer = f.bot_developers


bot.load_extension("jishaku")
bot.load_extension('cog.info')
bot.load_extension('cog.admin')
bot.load_extension('cog.other')
bot.load_extension('cog.moderation')
bot.load_extension('cog.report')
bot.load_extension('cog.fun')
bot.load_extension('cog.help')


@bot.event
async def on_command(ctx):
    e = discord.Embed(title="コマンド実行ログ", description=f"実行分:`{ctx.message.clean_content}`")
    e.set_author(name=f"{ctx.author}({ctx.author.id})", icon_url=ctx.author.avatar_url_as(static_format="png"))
    e.add_field(name="実行サーバー", value=f"{ctx.guild.name}({ctx.guild.id})")
    e.add_field(name="実行チャンネル", value=ctx.channel.name)

    e.timestamp = ctx.message.created_at
    ch = bot.get_channel(803558816834650152)

    await ch.send(embed=e)


@bot.event
async def on_ready():
    activity = discord.Game(name="y/helpsで確認", type=3)
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    print("Bot is ready!")



@bot.event
async def on_user_update(before, after):
    if before.name != after.name:
        e = discord.Embed(title="ニックネームが変わりました", color=0x5d00ff, timestamp=datetime.utcnow())
        fields = [("Before", before.name, False), ("After", after.name, False)]

        for name, value, inline in fields:
            e.add_field(name=name, value=value, inline=inline)

        channel = discord.utils.get(before.get_channels, name="幽々子ログ")
        await channel.send(embed=e)


@bot.event
async def on_guild_channel_create(channel):
    e = discord.Embed(title="チャンネル作成", timestamp=channel.created_at,color=0x5d00ff)
    e.add_field(name="チャンネル名", value=channel.mention)
    channel = discord.utils.get(channel.guild.channels, name="幽々子ログ")
    await channel.send(embed=e)

@bot.event
async def on_member_ban(g, user):
    guild = bot.get_guild(g.id)
    bl = await guild.audit_logs(limit=1, action=discord.AuditLogAction.ban).flatten()
    e = discord.Embed(title="ユーザーのban", color=0x5d00ff)
    e.add_field(name="ユーザー名", value=str(user))
    e.add_field(name="実行者", value=str(bl[0].user))
    channel = discord.utils.get(bot.get.channels, name="幽々子ログ")
    await channel.send(embed=e)

@bot.event
async def on_invite_create(invite):
    e = discord.Embed(title="サーバー招待の作成", color=0x5d00ff)
    e.add_field(name="作成ユーザー", value=str(invite.inviter))
    e.add_field(name="使用可能回数", value=str(invite.max_uses))
    e.add_field(name="使用可能時間", value=str(invite.max_age))
    e.add_field(name="チャンネル", value=str(invite.channel.mention))
    e.add_field(name="コード", value=str(invite.code))
    channel = discord.utils.get(invite.guild.channels, name="幽々子ログ")
    await channel.send(embed=e)




@bot.event
async def on_message_delete(message):
    if not message.author.bot:
        e = discord.Embed(title="メッセージ削除", color=0x5d00ff)
        e.add_field(name="メッセージ", value=message.content)
        e.add_field(name="メッセージ送信者", value=message.author.mention)
        e.add_field(name="メッセージチャンネル", value=message.channel.mention)
        e.add_field(name="メッセージのid", value=message.id)

        channel = discord.utils.get(message.guild.channels, name="幽々子ログ")
        await channel.send(embed=e)

@bot.event
async def on_message_edit(before, after):

    embed = discord.Embed(
        title="メッセージが編集されました",
        timestamp=after.created_at,
        description = f"<#{before.channel.id}>で<@!{before.author.id}>がメッセージを編集しました",
        colour = discord.Colour(0x5d00ff)
        )
    embed.set_author(name=f'{before.author.name}#{before.author.discriminator}', icon_url=before.author.avatar_url)
    embed.set_footer(text=f"Author ID:{before.author.id} • Message ID: {before.id}")
    embed.add_field(name='Before:', value=before.content, inline=False)
    embed.add_field(name="After:", value=after.content, inline=False)
    embed.add_field(name="メッセージのURL", value=after.jump_url)
    channel = discord.utils.get(after.guild.channels, name="幽々子ログ")
    await channel.send(embed=embed)




@bot.event
async def on_guild_role_create(role):
    e = discord.Embed(title="役職の作成", color=0x5d00ff,timestamp=role.created_at)
    e.add_field(name="役職名", value=role.name)
    e.add_field(name="役職名", value=role.id)


    ch = discord.utils.get(role.guild.channels, name="幽々子ログ")
    await ch.send(embed=e)

@bot.event
async def on_guild_role_delete(role):
    e = discord.Embed(title="役職の削除", color=0x5d00ff)
    e.add_field(name="役職名", value=role.name)

    ch = discord.utils.get(role.guild.channels, name="幽々子ログ")
    await ch.send(embed=e)


@bot.event
async def on_guild_channel_delete(channel):
    e = discord.Embed(title="チャンネル削除", color=0x5d00ff)
    e.add_field(name="チャンネル名", value=channel.name)
    ch = discord.utils.get(channel.guild.channels, name="幽々子ログ")
    await ch.send(embed=e)




@bot.event
async def on_guild_channel_update(before, after):
    channel = discord.utils.get(before.guild.channels, name="幽々子ログ")
    embed = discord.Embed(title="Channel Name Updated", description="チャンネルがアップデートしました",color=0x5d00ff)
    embed.add_field(name="Old name", value=f"The old name was: {before}.", inline=True)
    embed.add_field(name="New name", value=f"The old name was: {after}.", inline=False)
    await channel.send(embed=embed)

@bot.event
async def on_voice_state_update(before, after):
    if before.voice.voice_channel is None and after.voice.voice_channel is not None:
        for channel in before.server.channels:
            if channel.name == 'あざ':
                await bot.send_message(channel, "Howdy")




@bot.event
async def on_command_error(ctx, error):
    ch = 799505924280156192
    embed = discord.Embed(title="エラー情報", description="", color=0xf00)
    embed.add_field(name="エラー発生サーバー名", value=ctx.guild.name, inline=False)
    embed.add_field(name="エラー発生サーバーID", value=ctx.guild.id, inline=False)
    embed.add_field(name="エラー発生ユーザー名", value=ctx.author.name, inline=False)
    embed.add_field(name="エラー発生ユーザーID", value=ctx.author.id, inline=False)
    embed.add_field(name="エラー発生コマンド", value=ctx.message.content, inline=False)
    embed.add_field(name="発生エラー", value=error, inline=False)
    m = await bot.get_channel(ch).send(embed=embed)
    await ctx.send("エラーが発生しました")



bot.run(f.TOKEN)



