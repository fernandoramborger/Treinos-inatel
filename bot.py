import discord
from discord.ext import commands, tasks
from datetime import datetime
import pymongo
from pymongo import MongoClient
import pytz
from discord.ui import Select, View

fuso_horario = pytz.timezone('America/Sao_Paulo')

cluster = MongoClient(
    "mongodb+srv://cdghubinatel:CodersDG21@cluster0.honcgzn.mongodb.net/?retryWrites=true&w=majority"
)

db = cluster["Treinos_inatel"]
# collection = db["Inatel esports"]

collection_jogadores = db['Jogadores']
collection_treinos_marcados = db['Treinos marcados']
collection_treinos_realizados = db['Treinos realizados']
collection_registros = db['Registros de entradas e saídas']

intents = discord.Intents.default()
intents.message_content = True

global treinos_atuais
treinos_atuais = []

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(bot.user.name)
    print('Bot online!')
    await bot.change_presence(activity=discord.Streaming(
        name='!comandos', url='https://www.twitch.tv/inatel_esports'))
    myLoop.start()


@bot.command()
async def comandos(message):
    embed = discord.Embed(
        title="Comando do bot de treinos",
        color=0xff810a,
        description=
        '''!treinos: Mostra todos os treinos de todas as modalidades que estão marcados.

          !iniciartreino: Inicia um treino para o horário da mensagem

          No horário do treino, será criada uma sala na categoria da sua modalidade. Utilize essa sala para treinar e validar suas horas de treino e conseguir suas horas em AC. Se forem necessárias 2 salas de treino, aguarde 1 minuto desde a criação da primeira sala (o horário de sua criação aparece no próprio nome da sala) e utilize o comando !iniciartreino. Suas entradas e saídas dos treinos estarão registradas no canal de texto #bot-treinos'''
    )

    embed.set_thumbnail(
        url=
        'https://assets.faceit-cdn.net/hubs/avatar/f376e3e8-3d6d-4f2b-ba0a-51688c4d0dcf_1587333572197.jpg'
    )
    await message.channel.send(embed=embed)


@bot.command()
async def treinos(message):
    resposta = ''
    treinos = collection_treinos_marcados.find({})
    modalidades = []
    dias = []
    horarios = []
    for i in treinos:
        for key, value in i.items():

            if (key == "modalidade_treino"):
                modalidades.append(value)
            if (key == "dias_semana_treino"):
                dias.append(value)
            if (key == "horas_treino"):
                horarios.append(value)

    resposta = discord.Embed(title="\n",
                             color=0xe6d733,
                             description='Todos os treinos marcados:')

    for i in range(len(modalidades)):
        for j in range(len(dias[i])):
            resposta.add_field(name=modalidades[i],
                               value=dias[i][j] + ' ' + horarios[i][j] + 'h',
                               inline=True)

    resposta.set_author(
        name="Inatel Treinos",
        icon_url="https://inatel.br/cdghub/images/inatel-e-sports.jpg")
    await message.channel.send(embed=resposta)


@tasks.loop(seconds=60)
async def myLoop():
    guild = bot.get_guild(1000855799482028062)
    canal_msg = bot.get_channel(1166791952491102268)

    datetime_atual = datetime.now(fuso_horario)
    dia_semana_atual = datetime_atual.weekday()
    if dia_semana_atual == 0:
        dia_semana_atual = 'Segunda'
    elif dia_semana_atual == 1:
        dia_semana_atual = 'Terça'
    elif dia_semana_atual == 2:
        dia_semana_atual = 'Quarta'
    elif dia_semana_atual == 3:
        dia_semana_atual = 'Quinta'
    elif dia_semana_atual == 4:
        dia_semana_atual = 'Sexta'
    elif dia_semana_atual == 5:
        dia_semana_atual = 'Sábado'
    elif dia_semana_atual == 6:
        dia_semana_atual = 'Domingo'

    for j in treinos_atuais:

        treino_realizado = collection_treinos_realizados.find_one(
            {"_id": j}, {
                "_id": 1,
                "modalidade_treino": 1,
                "criado_em": 1
            })

        inicio_treino = treino_realizado['criado_em']
        inicio_treino = datetime.strptime(inicio_treino, "%d/%m/%Y %H:%M:%S")
        hora_atual = datetime.now(fuso_horario).strftime("%d/%m/%Y %H:%M:%S")
        hora_atual = datetime.strptime(hora_atual, "%d/%m/%Y %H:%M:%S")
        duracao_treino = hora_atual - inicio_treino
        duracao_treino = duracao_treino.total_seconds()

        if duracao_treino > 9000:
            try:
                canal_delete = bot.get_channel(j)
                members = canal_delete.members
                for membro in members:
                    saida = datetime.now(fuso_horario).strftime("%H:%M")
                    collection_registros.update_one({"_id": str(j) + membro.name},
                                                    {"$set": {
                                                        "saida": saida
                                                    }})
                    inicio_treino = collection_registros.find_one(
                        {"_id": str(j) + membro.name}, {"entrada": 1})
                    hora_inico = datetime.strptime(inicio_treino['entrada'], '%H:%M')
                    hora_saida = datetime.strptime(saida, '%H:%M')
                    total_horas = hora_saida - hora_inico
                    total_horas = round((total_horas.total_seconds() / 3600), 2)
                    collection_jogadores.update_one(
                        {"nome_discord": membro.name},
                        {"$inc": {
                            "numero_horas_total": total_horas
                        }})
                    nome_canal = canal_delete.name
                    treinos_atuais.remove(j)
                    await canal_delete.delete()
                    embed = discord.Embed(
                        title=nome_canal + " encerrado!",
                        color=0xf56161,
                        description=
                        'As horas de treino de todos os membros foram contabilizadas. \n \nAté a próxima!'
                    )
                    embed.set_thumbnail(
                        url=
                        'https://static.wikia.nocookie.net/leagueoflegends/images/d/dc/M%27Pengu_Emote.png/revision/latest/scale-to-width-down/250?cb=20181207233503'
                    )
                    embed.add_field(name="Horário de início",
                                    value=str(hora_inico.hour).zfill(2) + ":" +
                                          str(hora_inico.minute).zfill(2),
                                    inline=True)
                    embed.add_field(name="Horário de encerramento",
                                    value=str(hora_saida.hour).zfill(2) + ":" +
                                          str(hora_saida.minute).zfill(2),
                                    inline=True)
                    embed.set_footer(
                        text='"Me jogue aos lobos e eu... Aiaiai o lobo me mordeu!"')
                    await canal_msg.send(embed=embed)
                treinos_atuais.remove(j)
                await canal_delete.delete()
            except:
                print('Canal já foi deletado')

    treinos = collection_treinos_marcados.find(
        {"dias_semana_treino": dia_semana_atual}, {
            "_id": 0,
            "modalidade_treino": 1,
            "horas_treino": 1,
            "dias_semana_treino": 1
        })
    for i in treinos:
        indice_hora = i['dias_semana_treino'].index(dia_semana_atual)
        modalidade_treino = (i['modalidade_treino'])
        hora_treino = (i['horas_treino'][indice_hora])
        current_time = datetime.now(fuso_horario).strftime("%H:%M")

        if hora_treino == current_time:
            category = discord.utils.get(guild.categories, name=modalidade_treino)
            await category.create_voice_channel(name='Treino ' + modalidade_treino +
                                                     ' ' + hora_treino)

            resposta = discord.Embed(title="\n",
                                     color=0xe6d733,
                                     description='Sala de treino de ' +
                                                 modalidade_treino + ' foi criada. Bom treino!')

            resposta.set_author(
                name="Inatel Treinos",
                icon_url="https://inatel.br/cdghub/images/inatel-e-sports.jpg")
            await canal_msg.send(embed=resposta)

            channel = discord.utils.get(guild.channels,
                                        name='Treino ' + modalidade_treino + ' ' +
                                             hora_treino)
            channel_treino_id = channel.id
            jogadores_presentes = []
            criacao = datetime.now(fuso_horario).strftime("%d/%m/%Y %H:%M:%S")
            try:
                collection_treinos_realizados.insert_one({
                    "_id":
                        channel_treino_id,
                    "modalidade_treino_realizado":
                        modalidade_treino,
                    "jogadores_presentes":
                        jogadores_presentes,
                    "criado_em":
                        criacao
                })
            except:
                print('Id duplicado')
            treinos_atuais.append(channel_treino_id)

            @bot.event
            async def on_voice_state_update(member, before, after):
                nome = member.name

                if after.channel is not None:
                    if after.channel.id in treinos_atuais:
                        try:
                            collection_treinos_realizados.update_one(
                                {"_id": after.channel.id},
                                {"$addToSet": {
                                    "jogadores_presentes": nome
                                }})
                            collection_registros.insert_one({
                                "_id":
                                    str(after.channel.id) + nome,
                                "jogador":
                                    "{}".format(nome),
                                "entrada":
                                    datetime.now(fuso_horario).strftime("%H:%M")
                            })
                            embed = discord.Embed(
                                title="Treino iniciado!",
                                color=0x33e636,
                                description='Seu treino foi iniciado, ' + nome +
                                            '. Suas horas de treino serão contabilizadas a partir de agora até sua última saída dessa chamada. \n \nBom treino!'
                            )
                            if member.avatar is None:
                                embed.set_author(name=nome, icon_url=member.default_avatar)
                            else:
                                embed.set_author(name=nome, icon_url=member.avatar)
                            embed.set_footer(
                                text='"Me jogue aos lobos e eu... Aiaiai o lobo me mordeu!"')
                            embed.set_thumbnail(
                                url=
                                'https://static.wikia.nocookie.net/leagueoflegends/images/8/82/Go_Team%21_Emote.png/revision/latest?cb=20230316211925'
                            )
                            await canal_msg.send(embed=embed)
                        except:
                            print('Entrada já registrada')
                elif before.channel.id in treinos_atuais:
                    saida = datetime.now(fuso_horario).strftime("%H:%M")
                    collection_registros.update_one(
                        {"_id": str(before.channel.id) + nome},
                        {"$set": {
                            "saida": saida
                        }})

                    inicio_treino = collection_registros.find_one(
                        {"_id": str(before.channel.id) + nome}, {"entrada": 1})
                    hora_inico = datetime.strptime(inicio_treino['entrada'], '%H:%M')
                    hora_saida = datetime.strptime(saida, '%H:%M')
                    total_horas = hora_saida - hora_inico
                    total_horas = round((total_horas.total_seconds() / 3600), 2)

                    collection_jogadores.update_one(
                        {"nome_discord": nome},
                        {"$inc": {
                            "numero_horas_total": total_horas
                        }})

                    embed = discord.Embed(
                        title="Treino encerrado!",
                        color=0xf56161,
                        description='Sua saída foi registrada, ' + nome +
                                    '. Suas horas de treino serão contabilizadas. \n \nAté a próxima!'
                    )
                    if member.avatar is None:
                        embed.set_author(name=nome, icon_url=member.default_avatar)
                    else:
                        embed.set_author(name=nome, icon_url=member.avatar)
                    embed.set_thumbnail(
                        url=
                        'https://static.wikia.nocookie.net/leagueoflegends/images/d/dc/M%27Pengu_Emote.png/revision/latest/scale-to-width-down/250?cb=20181207233503'
                    )
                    embed.add_field(name="Horário de entrada",
                                    value=str(hora_inico.hour).zfill(2) + ":" +
                                          str(hora_inico.minute).zfill(2),
                                    inline=True)
                    embed.add_field(name="Horário de saída",
                                    value=str(hora_saida.hour).zfill(2) + ":" +
                                          str(hora_saida.minute).zfill(2),
                                    inline=True)
                    embed.set_footer(
                        text='"Me jogue aos lobos e eu... Aiaiai o lobo me mordeu!"')
                    await canal_msg.send(embed=embed)

            collection_treinos_marcados.delete_many({'treinos_temp': 'treinos_temp'})


@bot.command()
async def iniciartreino(message):
    dias_semana_treino = []
    horas_treino = []
    cargos = message.author.roles
    nomes_cargo = [role.name for role in cargos]

    select = Select(
        min_values=1,
        max_values=1,
        placeholder="Selecione a modalidade",
        options=[
            discord.SelectOption(
                label='CS GO Fem'
            ),
            discord.SelectOption(
                label='CS GO'
            ),
            discord.SelectOption(
                label='Valorant Fem'
            ),
            discord.SelectOption(
                label='Valorant'
            ),
            discord.SelectOption(
                label='League of Legends Fem'
            ),
            discord.SelectOption(
                label='League of Legends'
            ),
            discord.SelectOption(
                label='Hearthstone'
            ),
            discord.SelectOption(
                label='FIFA'
            ),
            discord.SelectOption(
                label='TFT'
            ),
        ])

    async def my_callback(interaction):

        modalidade_tr = select.values[0]

        if modalidade_tr in nomes_cargo:
            resposta = discord.Embed(title="\n",
                                     color=0xe6d733,
                                     description='Sua sala de treino de ' +
                                                 modalidade_tr +
                                                 ' será criada em no máximo 1 minuto, aguarde.')

            resposta.set_author(
                name="Inatel Treinos",
                icon_url="https://inatel.br/cdghub/images/inatel-e-sports.jpg")

            treinos = collection_treinos_marcados.find(
                {"dias_semana_treino": dia_semana}, {
                    "_id": 0,
                    "modalidade_treino": 1,
                    "horas_treino": 1,
                    "dias_semana_treino": 1
                })

            results = list(treinos)

            if len(results) == 0:
                collection_treinos_marcados.insert_one({
                    'treinos_temp': 'treinos_temp',
                    "modalidade_treino": modalidade_tr,
                    "dias_semana_treino": dias_semana_treino,
                    "horas_treino": horas_treino
                })

            for i in results:
                indice_hora = i['dias_semana_treino'].index(dia_semana)
                modalidade_treino = (i['modalidade_treino'])
                hora_treino_busca = (i['horas_treino'][indice_hora])
                if hora_treino_busca == hora_treino_temp and modalidade_treino == modalidade_tr:
                    resposta = discord.Embed(title="\n",
                                             color=0xe6d733,
                                             description='Já existe um treino marcado para esse horário!')
                    resposta.set_author(
                        name="Inatel Treinos",
                        icon_url="https://inatel.br/cdghub/images/inatel-e-sports.jpg")

                else:
                    collection_treinos_marcados.insert_one({
                        'treinos_temp': 'treinos_temp',
                        "modalidade_treino": modalidade_tr,
                        "dias_semana_treino": dias_semana_treino,
                        "horas_treino": horas_treino
                    })

        else:
            resposta = discord.Embed(
                title="\n",
                color=0xe6d733,
                description=
                'Você não possui cargo dessa modalidade e não pode criar um treino para ela.'
            )

            resposta.set_author(
                name="Inatel Treinos",
                icon_url="https://inatel.br/cdghub/images/inatel-e-sports.jpg")

        await interaction.response.edit_message(content=None, embed=resposta, view=None)

    select.callback = my_callback
    view = View()
    view.add_item(select)

    await message.channel.send('⚠ Escolha a modalidade do treino: \n ', view=view)

    datetime_atual = datetime.now(fuso_horario)
    dia_semana = datetime_atual.weekday()
    if dia_semana == 0:
        dia_semana = 'Segunda'
    elif dia_semana == 1:
        dia_semana = 'Terça'
    elif dia_semana == 2:
        dia_semana = 'Quarta'
    elif dia_semana == 3:
        dia_semana = 'Quinta'
    elif dia_semana == 4:
        dia_semana = 'Sexta'
    elif dia_semana == 5:
        dia_semana = 'Sábado'
    elif dia_semana == 6:
        dia_semana = 'Domingo'

    current_time = datetime.now(fuso_horario)
    minuto = str(current_time.minute + 1).zfill(2)
    hora = str(current_time.hour).zfill(2)

    hora_treino_temp = hora + ':' + minuto

    dias_semana_treino.append(dia_semana)
    horas_treino.append(hora_treino_temp)


TOKEN = '<TOKEN_BOT_DISCORD>'



bot.run(TOKEN)
