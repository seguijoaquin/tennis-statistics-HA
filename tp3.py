#!/usr/bin/env python3

import glob
from datetime import datetime

def main():
    # Concatenación
    matches = []
    for filename in glob.glob('./client/data/atp_matches_*.csv'):
        with open(filename, 'r') as file:
            file.readline()
            for line in iter(file.readline, ''):
                data = line.split(',')
                tourney_date = data[2]
                surface = data[3]
                minutes = 0 if data[9] == '' else float(data[9])
                winner_id = data[4]
                loser_id = data[5]
                matches.append([winner_id, loser_id, surface, minutes, None, None,
                                None, None, None, None, tourney_date])

    # Join
    players = {}
    with open('./client/data/atp_players.csv', 'r') as file:
        file.readline()
        for line in iter(file.readline, ''):
            data = line.split(',')
            players[data[0]] = data[1:5]

    for match in matches:
        for i in range(2):
            data = players[match[i]]
            match[i + 4] = data[0] + ' ' + data[1] # Name
            match[i + 6] = data[2] # Hand
            if data[3] == '':
                birthdate = datetime.today()
            else:
                birthdate = datetime.strptime(data[3], '%Y%m%d')

            age = compute_age(birthdate, datetime.strptime(match[-1], '%Y%m%d'))
            match[i + 8] = age

    # Tiempo promedio
    times = {'Clay': [0,0], 'Hard': [0,0], 'Grass': [0,0], 'Carpet':[0,0]}
    for match in matches:
        surface = match[2]
        minutes = match[3]
        if minutes == 0 or surface in ('', 'None'):
            continue
        times[surface][0] += minutes
        times[surface][1] += 1

    print("Clay: " + str(times['Clay'][0] / times['Clay'][1]))
    print("Grass-Carpet: " + str((times['Grass'][0] + times['Carpet'][0]) / (times['Grass'][1] + times['Carpet'][1])))
    print("Hard: " + str(times['Hard'][0] / times['Hard'][1]))

    # Victorias Zurdos vs Diestros
    r_wins = 0.0
    l_wins = 0.0
    for match in matches:
        w_hand = match[6]
        l_hand = match[7]
        if w_hand == 'R' and l_hand != w_hand:
            r_wins += 1
        elif (w_hand == 'L' or w_hand == 'U') and l_hand != w_hand:
            l_wins += 1

    print("R Victories: " + str(100 * r_wins / (r_wins + l_wins)) + "%")
    print("L Victories: " + str(100 * l_wins / (r_wins + l_wins)) + "%")

    # Victorias
    for match in matches:
        w_age = match[8]
        l_age = match[9]
        if w_age <= 0 or l_age <= 0:
            continue
        if w_age - l_age >= 20:
            print("{}\t{}\t{}\t{}".format(w_age, match[4], l_age, match[5]))


def compute_age(birthdate, tourney_date):
    years = tourney_date.year - birthdate.year
    if tourney_date.month < birthdate.month or (tourney_date.month == birthdate.month and tourney_date.day < birthdate.day):
        years -= 1
    return years

if __name__ == '__main__':
    main()
