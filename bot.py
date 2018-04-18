import discord
import json
import requests
import logging
from lxml import html
from random import randint
from difflib import get_close_matches

client = discord.Client()

# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)


with open('dex.json') as dex_file:
    dex = json.load(dex_file)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):
    # ignores messages in channels where the bot doesn't have send message permission
    if not message.server.me.permissions_in(message.channel).send_messages:
        return

    # !pd
    if message.content.startswith('!pd '):
        await pd(message)
    # !pdl
    elif message.content.startswith('!pdl '):
        await pdl(message)
    # !tos
    elif message.content.startswith('!tos'):
        await client.send_message(message.channel, 'https://www.nianticlabs.com/terms/pokemongo/en')
    # !fusion
    elif message.content.startswith('!fusion ') or message.content.startswith('.f '):
        if message.channel.id == '204069825658617866' or message.channel.id == '267092705975205899':
            await client.send_message(message.channel, 'Please use the <#286231618207612928> channel.')
        else:
            if len(message.content.split()) == 2 and message.content.split()[1].lower() == 'random':
                await fusion(message, requests.get('http://pokemon.alexonsager.net'))
            elif len(message.content.split()) == 3:
                name1 = fix_odd_names(message.content.split()[1])
                name2 = fix_odd_names(message.content.split()[2])
                if name1 == 'random':
                    mon1_id = randint(0, 151)
                    mon2_id = name_to_id(name2)
                elif name2 == 'random':
                    mon1_id = name_to_id(name1)
                    mon2_id = randint(0, 151)
                else:
                    mon1_id = name_to_id(name1)
                    mon2_id = name_to_id(name2)
                if mon1_id > 151 or mon2_id > 151:
                    await client.send_message(message.channel, 'Sorry, this command only works for Gen 1 Pokémon.')
                elif mon1_id != 0 and mon2_id != 0:
                    try:
                        await fusion(message, requests.get('http://pokemon.alexonsager.net/{}/{}'.format(mon1_id,
                                                                                                         mon2_id)))
                    except discord.Forbidden:
                        await client.send_message(message.channel, 'I don\'t have permission.')
                else:
                    await client.send_message(message.channel, 'You probably misspelled something.')
            elif len(message.content.split()) == 4:
                if fix_odd_names(message.content.split()[1]) == 'mr-mime':
                    mon1_id = name_to_id('mr-mime')
                    if message.content.split()[3] == 'random':
                        mon2_id = randint(0, 151)
                    else:
                        mon2_id = name_to_id(message.content.split()[3])
                    await fusion(message, requests.get('http://pokemon.alexonsager.net/{}/{}'.format(mon1_id, mon2_id)))
                elif fix_odd_names(message.content.split()[2]) == 'mr-mime':
                    if message.content.split()[1] == 'random':
                        mon1_id = randint(0, 151)
                    else:
                        mon1_id = name_to_id(message.content.split()[1])
                    mon2_id = name_to_id('mr-mime')
                    await fusion(message, requests.get('http://pokemon.alexonsager.net/{}/{}'.format(mon1_id, mon2_id)))
            else:
                await client.send_message(message.channel, 'Sorry, I don\'t understand.')

    # !type
    elif message.content.startswith('!type'):
        if message.channel.id == '204069825658617866' or message.channel.id == '267092705975205899':
            await client.send_message(message.channel, 'Please use the <#286231618207612928> channel.')
        else:
            if len(message.content.split()) > 2:
                await client.send_message(message.channel, 'Sorry, I don\'t understand')
            elif len(message.content.split()) > 1:
                output = type_info(message.content.split()[1].lower())
                await client.send_message(message.channel, output)
                # !moves
    elif message.content.startswith('!moves '):
        if message.channel.id == '204069825658617866' or message.channel.id == '202145713952522241':
            await client.send_message(message.channel, 'Please use <#286231618207612928>')
        else:
            name = message.content[7:]
            if name_to_id(name) == 0:
                await client.send_message(message.channel, 'Sorry, I don\'t understand. Try again.')
            else:
                try:
                    await client.send_message(message.channel,
                                              moves_output(fix_odd_names(name), True))
                except discord.HTTPException:
                    await client.send_message(message.channel, moves_output(fix_odd_names(name), False))
    elif message.content.startswith('!raidinfo'):
        if message.content == '!raidinfo':
            await client.send_message(message.channel, 'Try !raidinfo <raid boss>')
        else:
            with open('raidbosses.json') as info:
                bossinfo = json.load(info)
            mon = message.content[10:].lower()
            if mon not in bossinfo:
                await client.send_message(message.channel, 'Sorry, I don\'t understand.')
            else:
                output = '**{}** {}'.format(mon.capitalize(), ':star:' * int(bossinfo[mon]['level']))
                output += '\n\nLvl 20 CP Range: {} - {}\nLvl 25 CP Range: {} - {}'.format(
                    bossinfo[mon]['min_cp'],
                    bossinfo[mon]['max_cp'],
                    bossinfo[mon]['boosted_min_cp'],
                    bossinfo[mon]['boosted_max_cp'])
                weather1 = bossinfo[mon]['boosted_weather'][0]
                weather2 = ''
                if len(bossinfo[mon]['boosted_weather']) > 1:
                    weather2 = bossinfo[mon]['boosted_weather'][1]
                output += '\nBoosted during {}'.format(weather1)
                if weather2:
                    output += ' or {} weather'.format(weather2)
                else:
                    output += ' weather'
                output += '\n\nWeak to: '
                for type in bossinfo[mon]['weak_to']:
                    output += '{} '.format(type_to_emoji(type))
                if bossinfo[mon]['double_weak_to']:
                    output += '\nDouble weak to: '
                    for type in bossinfo[mon]['double_weak_to']:
                        output += '{} '.format(type_to_emoji(type))
                output += '\n\nCatch rate: {}%'.format(bossinfo[mon]['catch_rate'])
                await client.send_message(message.channel, output)
    elif client.user.mentioned_in(message) and 'help' in message.content and not message.mention_everyone:
        await client.send_message(message.channel, '__Commands:__\n```'
                                                   '!pd <pokemon>              - Pokémon information\n'
                                                   '!pdl <pokemon>             - !pd without the movesets\n'
                                                   '!moves <pokemon>           - Full list of movesets\n'
                                                   '!type <type> or <pokemon>  - Type matchups\n'
                                                   '!raidinfo <raidboss>       - Info about a raid boss\n```')
    # role request
    if message.server.id == '330217404669886465':
        valid_roles = ['mystic', 'valor', 'instinct', 'san rafael', 'ross valley', 'corte madera', 'twin cities',
                       'novato', 'tiburon', 'mill valley', 'sausalito', 'marinwood-tl', 'central marin', 'ex raids',
                       'lvl40', 'lvl39', 'lvl38', 'lvl37', 'lvl36', 'lvl35', 'lvl34', 'lvl33', 'lvl32', 'lvl31',
                       'lvl30', 'lvl29', 'lvl28', 'lvl27', 'lvl26', 'lvl25', 'lvl24', 'lvl23', 'lvl22', 'lvl17',
                       'lvl16']
        if message.content.startswith('!r '):
            split_message = message.content[3:].split(', ')
            requested_roles = []
            if len(split_message):
                for r in split_message:
                    r = r.lower()
                    if is_number(r):
                        r = 'lvl' + r
                        if r in valid_roles:
                            role = discord.utils.get(message.server.roles, name=r)
                            requested_roles.append(role)
                    elif r.lower() in valid_roles:
                        if r.lower() == 'marinwood-tl':
                            r = 'Marinwood-TL'
                        elif r.lower() == 'ex raids':
                            r = 'EX Raids'
                        else:
                            r = r.title()
                        role = discord.utils.get(message.server.roles, name=r)
                        requested_roles.append(role)
                    elif 'level' in r.lower():
                        r = 'lvl' + r.strip('level ')
                        if r in valid_roles:
                            role = discord.utils.get(message.server.roles, name=r)
                            requested_roles.append(role)
                    elif 'lvl ' in r.lower():
                        r = 'lvl' + r.strip('lvl ')
                        if r in valid_roles:
                            role = discord.utils.get(message.server.roles, name=r)
                            requested_roles.append(role)
                if len(requested_roles):
                    try:
                        await client.add_roles(message.author, *requested_roles)
                        if len(requested_roles) == 1:
                            await client.send_message(message.channel, 'Successfully added 1 role.')
                        else:
                            await client.send_message(message.channel,
                                                      'Successfully added {} roles. '.format(str(len(requested_roles))))
                    except discord.Forbidden:
                        await client.send_message(message.channel, 'I don\'t have permission.')
        if message.content.startswith('!remove '):
            if len(message.content.split()) > 1:
                role_name = message.content[8:].lower()
                for r in valid_roles:
                    if r in role_name:
                        if r.startswith('lvl'):
                            role = discord.utils.get(message.server.roles, name=r)
                        else:
                            role = discord.utils.get(message.server.roles, name=r.title())
                for r in role_name.split():
                    if is_number(r):
                        role = discord.utils.get(message.server.roles, name='lvl' + r)
                try:
                    await client.remove_roles(message.author, role)
                    await client.send_message(message.channel, 'Successfully removed 1 role.')
                except discord.Forbidden:
                    await client.send_message(message.channel, 'I don\'t have permission.')
            else:
                await client.send_message(message.channel, 'Sorry, I don\'t understand.')

    elif message.content.startswith('!servs'):
        count = 0
        user_count = 0
        # for server in client.servers:
        #     print(server.name + ' ' + str(server.member_count))
        #     user_count += server.member_count
        #     count += 1
        await client.send_message(message.channel, 'Servers: {}\nTotal users: {}'.format(str(count), str(user_count)))


async def pd(message):
    """Detailed Pokemon information"""
    if message.channel.id == '204069825658617866' or message.channel.id == '202145713952522241':
        await client.send_message(message.channel, 'Please use the <#286231618207612928> channel.')
    else:
        if len(message.content.split()) != 2:
            await client.send_message(message.channel, 'Sorry, I don\'t understand. Try again.')
        else:
            name = fix_odd_names(message.content.split()[1])
            if name_to_id(name) == 0 and not is_number(name) or is_number(name) and int(name) > 251:
                if len(get_close_matches(name, dex)):
                    await client.send_message(message.channel, 'There is no Pokémon with that name. Did you mean {}?'
                                              .format(get_close_matches(name, dex)[0].title()))
                else:
                    await client.send_message(message.channel, 'There is no Pokémon with that name. Try again.')
            else:
                if is_number(name):
                    with open('tsrdata.json') as tsr_data:
                        tsr = json.load(tsr_data)
                    poke_id = name
                    name = tsr[name]['speciesSlug']
                else:
                    poke_id = dex[name]['id']
                    # /home/ec2-user/testbot/sprites/{}.png /Users/luke/PycharmProjects/testbot/sprites/{}.png
                    await client.send_file(message.channel, '/home/ec2-user/testbot/sprites/{}.png'.format(poke_id))
                    if dex[name]['quick'] or dex[name]['offensive']:
                        await client.send_message(message.channel, pd_output(name, False))
                    else:
                        await client.send_message(message.channel, pd_output(name, True))


async def pdl(message):
    """!pd without the movesets"""

    name = fix_odd_names(message.content[5:])
    if name == 0:
        await client.send_message(message.channel, 'Sorry, I don\'t understand.')
    else:
        await client.send_message(message.channel, pd_output(name, True))


def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def name_to_id(name):
    """Converts a pokemon name into the corresponding ID
    
    Returns 0 if the name isn't found
    """

    name = fix_odd_names(name)
    if name not in dex:
        return 0
    else:
        return dex[name]['id']


def fix_odd_names(name):
    name = name.lower()
    if 'mr.' in name:
        name = 'mr-mime'
    elif '\'d' in name:
        name = 'farfetchd'
    elif '♂' in name:
        name = 'nidoran-m'
    elif '♀' in name:
        name = 'nidoran-f'
    return name


async def fusion(message, page):
    html_content = html.fromstring(page.content)
    img_url = html_content.xpath('//img[@id="pk_img"]/@src')[0]
    fusion_name = html_content.xpath('//span[@id="pk_name"]/text()')[0]
    em = discord.Embed(title=fusion_name, colour=0xFFFFFF)
    em.set_image(url=img_url)
    await client.send_message(message.channel, embed=em)


def type_to_emoji(type):
    """Converts a type to a Discord custom emoji"""

    emojis = {'water': '<:water:334734441220145175>',
              'steel': '<:steel:334734441312419851>',
              'rock': '<:rock:334734441194717195>',
              'psychic': '<:psychic:334734441639575552>',
              'poison': '<:poison:334734441584787456>',
              'normal': '<:normal:334734441538650112>',
              'ice': '<:ice:334734441421471756>',
              'ground': '<:ground:334734441421471747>',
              'grass': '<:grass:334734441501032448>',
              'ghost': '<:ghost:334734441232728066>',
              'flying': '<:flying:334734441161424900>',
              'fire': '<:fire:334734441165619202>',
              'fighting': '<:fighting:334734441425403905>',
              'fairy': '<:fairy:334734441501163530>',
              'electric': '<:electric:334734441089859586>',
              'dragon': '<:dragon:334734441505226762>',
              'dark': '<:dark:334734441119219713>',
              'bug': '<:bug:334734441509289984>'}
    return emojis[type.lower()]


def type_info(name):
    """Computes type effectiveness and builds the string to be output for !type"""

    with open('types.json') as json_file:
        types = json.load(json_file)
    output = ''
    if name_to_id(name) == 0:
        if name not in types:
            return 'Sorry, I don\'t understand'
        else:
            # Deals super effective damage (1.4x)
            output += '__Offensive:__\n{} deals 1.4x damage to '.format(name.capitalize())
            output += type_format(types[name]['atk_se'])
            # Deals not very effective damage (0.71x)
            output += '{} deals 0.71x damage to '.format(name.capitalize())
            output += type_format(types[name]['atk_nve'])
            # Deals immune damage (0.51x)
            if types[name]['atk_immune']:
                output += '{} deals 0.51x damage to '.format(name.capitalize())
                output += type_format(types[name]['atk_immune'])
            output += '\n'
            # Takes super effective damage (1.4x)
            output += '__Defensive:__\n{} takes 1.4x damage from '.format(name.capitalize())
            output += type_format(types[name]['def_se'])
            # Takes not very effective damage (0.71x)
            output += '{} takes 0.71x damage from '.format(name.capitalize())
            output += type_format(types[name]['def_nve'])
            if types[name]['def_immune']:
                output += '{} takes 0.51x damage from '.format(name.capitalize())
                output += type_format(types[name]['def_immune'])
    elif name_to_id(name) > 0:
        double_se = []
        se = []
        nve = []
        double_nve = []
        immune_nve = []
        double_immune = []
        type1 = dex[name]['types'][0]
        if len(dex[name]['types']) > 1:
            type2 = dex[name]['types'][1]
            for type in types[type1]['def_se']:
                if type in types[type2]['def_se']:
                    double_se.append(type)
                elif type not in types[type2]['def_nve'] and type not in types[type2]['def_immune']:
                    se.append(type)
                elif type in types[type2]['def_immune']:
                    nve.append(type)
            for type in types[type1]['def_nve']:
                if type in types[type2]['def_nve']:
                    double_nve.append(type)
                elif type not in types[type2]['def_se'] and type not in types[type2]['def_immune']:
                    nve.append(type)
                elif type in types[type2]['def_immune']:
                    immune_nve.append(type)
            for type in types[type1]['def_immune']:
                if type in types[type2]['def_immune']:
                    double_immune.append(type)
                elif type in types[type2]['def_nve']:
                    immune_nve.append(type)
                elif type in types[type2]['def_se']:
                    nve.append(type)
                else:
                    double_nve.append(type)
            for type in types[type2]['def_se']:
                if type not in types[type1]['def_nve'] and type not in types[type1]['def_immune'] and type not in \
                        double_se:
                    se.append(type)
            for type in types[type2]['def_nve']:
                if type not in types[type1]['def_se'] and type not in types[type1]['def_immune'] and type not in \
                        double_nve:
                    nve.append(type)
            for type in types[type2]['def_immune']:
                if type not in types[type1]['def_se'] and type not in types[type1]['def_nve'] and type not in \
                        double_immune and type not in immune_nve:
                    double_nve.append(type)
        else:
            for type in types[type1]['def_se']:
                se.append(type)
            for type in types[type1]['def_nve']:
                nve.append(type)
            for type in types[type1]['def_immune']:
                double_nve.append(type)
        if double_se:
            output += '{} takes 1.96x damage from '.format(name.capitalize())
            output += type_format(double_se)
        if se:
            output += '{} takes 1.4x damage from '.format(name.capitalize())
            output += type_format(se)
        if nve:
            output += '{} takes 0.71x damage from '.format(name.capitalize())
            output += type_format(nve)
        if double_nve:
            output += '{} takes 0.51x damage from '.format(name.capitalize())
            output += type_format(double_nve)
        if immune_nve:
            output += '{} takes 0.36x damage from '.format(name.capitalize())
            output += type_format(immune_nve)
        if double_immune:
            output += '{} takes 0.26x damage from '.format(name.capitalize())
            output += type_format(double_immune)
    return output


def type_format(types):
    output = ''
    if not types:
        output += 'nothing.\n'
    elif len(types) == 1:
        output += '**{}**.\n'.format(types[0].capitalize())
    elif len(types) == 2:
        output += '**{}** and '.format(types[0].capitalize())
        output += '**{}**.\n'.format(types[1].capitalize())
    else:
        for type in range(len(types) - 1):
            output += '**{}**, '.format(types[type].capitalize())
        output += 'and '
        output += '**{}**.\n'.format(types[len(types) - 1].capitalize())
    return output


def pd_output(name, pdl):
    """Builds the string to be displayed for the !pd or !pdl command"""

    with open('tsrdata.json') as tsr_data:
        tsr = json.load(tsr_data)
    with open('movetype.json') as movetype:
        move_type = json.load(movetype)
    pokemon_id = name_to_id(name)
    max_cp = dex[name]['max_cp']
    if pokemon_id < 252:
        base_atk = tsr[str(pokemon_id)]["base_attack"]
        base_def = tsr[str(pokemon_id)]['base_defense']
        base_sta = tsr[str(pokemon_id)]['base_stamina']
    else:
        base_atk = dex[name]['base_attack']
        base_def = dex[name]['base_defense']
        base_sta = dex[name]['base_stamina']
    types = dex[name]['types']
    output = '**#' + str(pokemon_id) + ' - ' + name.upper() + '**' + '\n' + 'Max CP: `' + str(max_cp) + '` Type: '
    if len(types) > 1:
        output += '{} | {}'.format(type_to_emoji(types[0]), type_to_emoji(types[1]))
    else:
        output += type_to_emoji(types[0])
    output += '\nATK: `{}` DEF: `{}` STA: `{}`'.format(base_atk, base_def, base_sta)
    if pdl:
        if len(dex[name]['evolution']) > 1:
            output += '\nEVOLUTION: '
            for i in range(len(dex[name]['evolution']) - 1):
                output += '{} -> '.format(dex[name]['evolution'][i][0].capitalize())
            if len(dex[name]['evolution'][
                               len(dex[name]['evolution']) - 1]) > 1:  # if pokemon has multiple same stage evos
                for i in range(len(dex[name]['evolution'][len(dex[name]['evolution']) - 1]) - 1):
                    output += '{}/'.format(dex[name]['evolution'][len(dex[name]['evolution']) - 1][i].capitalize())
            output += '{}\n'.format(dex[name]['evolution'][len(dex[name]['evolution']) - 1][
                                        len(dex[name]['evolution'][len(dex[name]['evolution']) - 1]) - 1].capitalize())
        return output
    if dex[name]['offensive']:  # check if pokemon has moves
        offensive = dex[name]['offensive']
        output += '\n__Attacking movesets:__\n'
        count = 0
        for i in range(len(offensive)):
            if count < 6:
                output += '[{}]{}{}{}, {}{}\n'.format(offensive[i]['rating'],
                                                      fix_indent(offensive[i]['rating']),
                                                      type_to_emoji(move_type[offensive[i]['quick'].strip(' *')]),
                                                      offensive[i]['quick'],
                                                      type_to_emoji(move_type[offensive[i]['charge'].strip(' *')]),
                                                      offensive[i]['charge'])
                count += 1
    else:
        quick = dex[name]['quick']
        output += '\n__Quick moves:__ \n```\n'
        for i in range(len(quick)):
            output += '{}\n'.format(quick[i])
    legendaries = ['articuno', 'moltres', 'zapdos', 'lugia', 'mewtwo', 'suicune', 'raikou', 'entei', 'ho-oh', 'groudon',
                   'kyogre', 'rayquaza', 'latios', 'latias']
    if dex[name]['defensive']:
        defensive = dex[name]['defensive']
        output += '\n'
        output += '__Defending movesets:__ \n'
        count = 0
        for i in range(len(defensive)):
            if count < 6:
                output += '[{}]{}{}{}, {}{}\n'.format(defensive[i]['rating'],
                                                      fix_indent(defensive[i]['rating']),
                                                      type_to_emoji(move_type[defensive[i]['quick'].strip(' *')]),
                                                      defensive[i]['quick'],
                                                      type_to_emoji(move_type[defensive[i]['charge'].strip(' *')]),
                                                      defensive[i]['charge'])
                count += 1
    elif name.lower() in legendaries:
        output += '\n'
    elif not dex[name]['defensive'] and dex[name]['offensive']:
        output += '\nNo defending movesets yet.\n'
    else:
        charge = dex[name]['charge']
        output += '```__Charge moves:__ \n```\n'
        for i in range(len(charge)):
            output += '{}\n'.format(charge[i])
        output += '```'
    if len(dex[name]['evolution']) > 1:
        output += 'EVOLUTION: '
        for i in range(len(dex[name]['evolution']) - 1):
            output += '{} -> '.format(dex[name]['evolution'][i][0].capitalize())
        if len(dex[name]['evolution'][len(dex[name]['evolution']) - 1]) > 1:   # if pokemon has multiple same stage evos
            for i in range(len(dex[name]['evolution'][len(dex[name]['evolution']) - 1]) - 1):
                output += '{}/'.format(dex[name]['evolution'][len(dex[name]['evolution']) - 1][i].capitalize())
        output += '{}\n'.format(dex[name]['evolution'][len(dex[name]['evolution']) - 1][
                                         len(dex[name]['evolution'][len(dex[name]['evolution']) - 1]) - 1].capitalize())
    output += '<https://pokemongo.gamepress.gg/pokemon/{}>'.format(pokemon_id)
    return output


def moves_output(name, pdl):
    """Formats the output for !moves"""

    if pdl:
        with open('movetype.json') as movetype:
            move_type = json.load(movetype)
    if dex[name]['offensive']:
        offensive = dex[name]['offensive']
        output = '**{}**\n__Attacking movesets:__\n'.format(name.upper())
        if not pdl:
            output += '```'
        for i in range(len(offensive)):
            if pdl:
                output += '[{}]{}{}{}, {}{}\n'.format(offensive[i]['rating'],
                                                      fix_indent(offensive[i]['rating']),
                                                      type_to_emoji(move_type[offensive[i]['quick'].strip(' *')]),
                                                      offensive[i]['quick'],
                                                      type_to_emoji(move_type[offensive[i]['charge'].strip(' *')]),
                                                      offensive[i]['charge'])
            else:
                output += '[{}]{}{} / {}\n'.format(offensive[i]['rating'],
                                                   fix_indent(offensive[i]['rating']),
                                                   offensive[i]['quick'],
                                                   offensive[i]['charge'])
    else:
        output = 'This Pokémon does not currently have any attacking movesets.'
    if dex[name]['defensive']:
        if not pdl:
            output += '```'
        else:
            output += '\n'
        defensive = dex[name]['defensive']
        output += '__Defending movesets:__ \n'
        if not pdl:
            output += '```'
        for i in range(len(defensive)):
            if pdl:
                output += '[{}]{}{}{}, {}{}\n'.format(defensive[i]['rating'],
                                                      fix_indent(defensive[i]['rating']),
                                                      type_to_emoji(move_type[defensive[i]['quick'].strip(' *')]),
                                                      defensive[i]['quick'],
                                                      type_to_emoji(move_type[defensive[i]['charge'].strip(' *')]),
                                                      defensive[i]['charge'])
            else:
                output += '[{}]{}{} / {}\n'.format(defensive[i]['rating'],
                                                   fix_indent(defensive[i]['rating']),
                                                   defensive[i]['quick'],
                                                   defensive[i]['charge'])
    else:
        output += '\nThis Pokémon does not currently have any defending movesets.'
    if not pdl:
        output += '```'
    return output


def fix_indent(rating):
    """Fixes the spacing between the moveset rating and the moves
    
    Returns three spaces if the rating is one character, two if it is two characters (A-, B-, etc)
    """

    if len(rating) == 1:
        return ' ' * 3
    else:
        return ' ' * 2


client.run('')