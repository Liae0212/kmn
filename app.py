from flask import Flask, render_template, redirect, request, session
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config["SESSION_TYPE"] = "filesystem"

#budowanie talii 108 kard
def buildDeck():
    deck = []
    colours = ["red","green","yellow","blue"]
    values = [0,1,2,3,4,5,6,7,8,9,"draw_two","skip","reverse"]
    wilds = ["black_wildcard","wild_draw_four"]
    for colour in colours:
        for value in values:
            cardVal = "{}_{}".format(colour,value)
            deck.append(cardVal)
            if value != 0:
                deck.append(cardVal)
    for i in range(4):
        deck.append(wilds[0])
        deck.append(wilds[1])
    return deck

#shuffle
def shuffleDeck(deck):
    for cardPos in range(len(deck)):
        randPos = random.randint(0,107)
        deck[cardPos], deck[randPos] = deck[randPos], deck[cardPos]
    return deck

#ciągniecie kart
def drawCards(numCards, deck):
    cardsDrawn = []
    if numCards <= len(deck):
        newDeck = buildDeck()
        newDeck = shuffleDeck(newDeck)
        session['unoDeck'].extend(newDeck)

    for x in range(numCards):
        cardsDrawn.append(deck.pop(0))
    return cardsDrawn


def checkValueOfACard(card):
    splitCard = card.split("_", 1)
    color = splitCard[0]
    value = splitCard[1]
    return value, color


def checkColorAndValOfDiscardedCard():
    splitCard = session['DISCARDS'][0].split("_", 1)
    currentColor = splitCard[0]
    currentVal = splitCard[1]
    return currentVal, currentColor


numCards = 5


def dealCards():
    for player in range(int(session['NUMPLAYERS'])):
        session['PLAYERS'].append(drawCards(7, session['unoDeck']))


def putTheCorrectStartingCard():
    values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    while True:
        session['DISCARDS'].insert(0, session['unoDeck'].pop(0))

        if any(value in session['DISCARDS'][0] for value in values):
            break


def players_exists():
    if not session.get('PLAYERS') or len(session['PLAYERS']) < 2:
        return False
    else:
        return True


def checkForMoves():
    session['CURRENTVAL'], session['CURRENTCOLOR'] = checkColorAndValOfDiscardedCard()
    session['PLAYABLE'] = ['magic_card']
    for card in session['PLAYERS'][session['PLAYERTURN']]:

        if session['DRAWCARDS'] != 0:
            if 'drawfour' in session['CURRENTVAL']:
                if session['CURRENTCOLOR'] == 'yellow':
                    if 'yellow_draw_two' in card or'wild_draw_four' in card:
                        session['PLAYABLE'].append(card)
                elif session['CURRENTCOLOR'] == 'blue':
                    if 'blue_draw_two' in card or'wild_draw_four' in card:
                        session['PLAYABLE'].append(card)
                elif session['CURRENTCOLOR'] == 'red':
                    if 'red_draw_two' in card or'wild_draw_four' in card:
                        session['PLAYABLE'].append(card)
                elif session['CURRENTCOLOR'] == 'green':
                    if 'green_draw_two' in card or'wild_draw_four' in card:
                        session['PLAYABLE'].append(card)
            elif session['CURRENTVAL'] in card or'wild_draw_four' in card:
                session['PLAYABLE'].append(card)
        elif session['DRAWCARDS'] == 0 and not session['DRAWN']:
            if session['PLAYEDVALUE'] == 0:
                if session['CURRENTCOLOR'] in card or session['CURRENTVAL'] in card or 'wild' in card or 'wild_draw_four' in card:
                    session['PLAYABLE'].append(card)
            elif session['PLAYEDVALUE'] != 0 and session['PLAYEDVALUE'] in card and session['PLAYEDVALUE'] != 'skip':
                session['PLAYABLE'].append(card)


def checkDrawCards():
    if session['DRAWCARDS'] != 0 and not session['MOVEMADE']:
        return True


def checkPick():
    if session['DRAWN']:
        return False


    if (not session['MOVEMADE'] and not session['PICKED'] and not session['DRAWN']):
        return True


def checkEndTurn():
    if session['WILDCARD']:
        return False

    elif session['DRAWFOUR']:
        return False

    elif session['DRAWCARDS'] != 0 and not session['DRAWN'] and not session['MOVEMADE']:
        return False

    elif session['DRAWCARDS'] == 0 and session['MOVEMADE']:
        return True

    elif (session['MOVEMADE'] or session['PICKED']):
        return True
    

def checkUno():
    current_player_hand = session['PLAYERS'][session['PLAYERTURN']]
    if len(current_player_hand) == 1 and not session.get('unoPlayer'):
        return True
    else:
        return False



def checkForFunctionalCards():
    if session['PLAYEDVALUE'] == "draw_two":
        session['DRAWCARDS'] += 2
    if session['PLAYEDVALUE'] == "draw_four":
        session['DRAWCARDS'] += 4
        session['DRAWFOUR'] = True

    if session['PLAYEDVALUE'] == "reverse":
        session['REVERSE'] *= -1

    if session['PLAYEDVALUE'] == "wildcard":
        session['WILDCARD'] = True

    if session['PLAYEDVALUE'] == "skip":
        session['WAIT'] += 1

    session.modified = True


def checkForButtons():
    if checkDrawCards():
        session['DRAWBUTTON'] = True
    else:
        session['DRAWBUTTON'] = False

    if checkPick():
        session['PICKBUTTON'] = True
    else:
        session['PICKBUTTON'] = False

    if checkEndTurn():
        session['ENDBUTTON'] = True
    else:
        session['ENDBUTTON'] = False
    
    if checkUno():
        session['UNO_PENDING'] = True
    else:
        session['UNO_PENDING'] = False

#kto wygrał
def checkWinner():
    if len(session['PLAYERS'][session['PLAYERTURN']]) == 0:
        session['WINNER'] = session['PLAYERTURN']
        session.modified = True
        return True
    elif len(session['PLAYERS'][session['PLAYERTURN']]) == 1:
        session['unoPlayer'] = session['PLAYERTURN']
    return False



@app.route('/')
def index():
    return redirect('/start')

@app.route('/start')
def start():
    return render_template('start.html')

@app.route('/board')
def board():
    if not players_exists():
        return redirect('/start')
    else:
        checkForMoves()
        checkForButtons()
        if not session['PLAYABLE'] and not session['PICKBUTTON'] and session['ENDBUTTON']:
            return redirect('/endturn')
        else:
            return render_template('board.html', drawbutton=session['DRAWBUTTON'], pickbutton=session['PICKBUTTON'],
                                   endbutton=session['ENDBUTTON'], uno_pending=session['UNO_PENDING'],playable=session['PLAYABLE'],
                                   players=session['PLAYERS'], playername=session['PLAYERNAME'],
                                   currentPlayer=session['PLAYERTURN'], numPlayers=session['NUMPLAYERS'],
                                   discards=session['DISCARDS'], wildcard=session['WILDCARD'],
                                   drawfour=session['DRAWFOUR'],
                                   wait=session['WAIT'], reverse=session['REVERSE'], drawcards=session['DRAWCARDS'])

@app.route('/reset', methods=['POST'])
def reset():
    session['WINNER'] = None

    session['PLAYERS'] = []
    session['PLAYERTURN'] = 0
    session['NUMPLAYERS'] = int(request.form['numPlayers'])
    session['PLAYERNAME'] = request.form.getlist("fname")

    session['DISCARDS'] = []
    session['CURRENTVAL'] = None
    session['CURRENTCOLOR'] = None
    session['PLAYABLE'] = []
    session['ENDBUTTON'] = False
    session['PICKBUTTON'] = False
    session['DRAWBUTTON'] = False
    session['UNO_PENDING'] = False

    session['PLAYEDVALUE'] = 0

    session['PLAYEDCOLOR'] = 0

    session['PICKED'] = False

    session['MOVEMADE'] = False

    session['DRAWCARDS'] = 0
    session['DRAWN'] = False

    session['WILDCARD'] = None

    session['DRAWFOUR'] = None

    session['REVERSE'] = 1

    session['WAIT'] = 0

    session['visits'] = 0

    session['unoDeck'] = buildDeck()
    session['unoDeck'] = shuffleDeck(session['unoDeck'])

    dealCards()
    putTheCorrectStartingCard()

    x = session['PLAYERNAME']
    y = session['NUMPLAYERS']
    if y == 2:
        if len(x) >= 2 and (x[0] == '' or x[1] == ''):
            return redirect('/start')
        else:
            return redirect('/board')
    elif y == 3:
        if len(x) >= 3 and (x[0] == '' or x[1] == '' or x[2] == ''):
            return redirect('/start')
        else:
            return redirect('/board')
    elif y == 4:
        if len(x) >= 4 and (x[0] == '' or x[1] == '' or x[2] == '' or x[3] == ''):
            return redirect('/start')
        else:
            return redirect('/board')

@app.route('/move/<discardedCard>')
def move(discardedCard):
    if not players_exists():
        return redirect('/start')
    else:
        for card in session['PLAYERS'][session['PLAYERTURN']]:
            if card == discardedCard:
                session['PLAYERS'][session['PLAYERTURN']].remove(card)
                session['DISCARDS'].insert(0, card)
                session['PLAYEDVALUE'], session['PLAYEDCOLOR'] = checkColorAndValOfDiscardedCard()

                checkForFunctionalCards()
                session['MOVEMADE'] = True
                session['PICKBUTTON'] = False
                session['PLAYABLE'] = []

                if checkWinner():
                    return redirect('/win')

    return redirect('/board')

@app.route('/pick')
def pick():
    if not session['PICKED']:
        if len(session['unoDeck']) == 0:
            session['unoDeck'] = buildDeck()
            for player in range(int(session['NUMPLAYERS'])):
                print(player[session['NUMPLAYERS']])
                for card in session['unoDeck']:
                    if card in player:
                        session['unoDeck'].remove(card)
                        print(session['unoDeck'])
            shuffleDeck(session['unoDeck'])

        if session['DRAWCARDS'] != 0:
            session['DRAWCARDS'] -= 1

        session['PLAYERS'][session['PLAYERTURN']].extend(drawCards(1, session['unoDeck']))
        session['PICKED'] = True
        session['PICKBUTTON'] = False
        session.modified = True

        # After drawing cards, reset UNO_PENDING
        session['UNO_PENDING'] = False

        # Penalize the player if they have one card left but didn't click Uno
        if len(session['PLAYERS'][session['PLAYERTURN']]) == 1:
            session['UNO_PENDING'] = True
        else:
            session['UNO_PENDING'] = False

    return redirect('/board')

@app.route('/uno')
def uno():
    current_player = session['PLAYERTURN']
    if current_player == session['unoPlayer']:
        session['unoPlayer'] = None
        return redirect('/board')
    else:
        # Penalize the player who clicked Uno at the wrong time
        session['PLAYERS'][current_player].extend(drawCards(2, session['unoDeck']))
        return redirect('/board')


@app.route('/draw')
def draw():
    session['PLAYERS'][session['PLAYERTURN']].extend(drawCards(int(session['DRAWCARDS']), session['unoDeck']))
    session['DRAWCARDS'] = 0
    session['PICKED'] = True
    session['MOVEMADE'] = True
    session['DRAWN'] = True
    session['DRAWBUTTON'] = False
    session['UNO_PENDING'] = False

    return redirect('/board')

@app.route('/endturn')
def endturn():
    session['PLAYABLE'] = []
    session['DRAWN'] = False

    current_player_index = session['PLAYERTURN']
    current_player_hand = session['PLAYERS'][current_player_index]

    # Penalize the player if they have one card left but haven't clicked Uno
    if len(current_player_hand) == 1 and current_player_index != session.get('unoPlayer'):
        # Penalize the player by drawing 2 extra cards
        session['PLAYERS'][current_player_index].extend(drawCards(2, session['unoDeck']))

    if session['REVERSE'] == 1:
        session['PLAYERTURN'] += 1

        if session['PLAYERTURN'] == session['NUMPLAYERS']:
            session['PLAYERTURN'] = 0

    elif session['REVERSE'] == -1:
        session['PLAYERTURN'] += -1

        if session['PLAYERTURN'] < 0:
            session['PLAYERTURN'] = int(session['NUMPLAYERS'] - 1)

    session['PLAYEDVALUE'] = 0
    session['PICKED'] = False
    session['MOVEMADE'] = False
    session['ENDBUTTON'] = False
    session['PICKBUTTON'] = False

    # After ending the turn, reset UNO_PENDING
    session['UNO_PENDING'] = False

    if session['WAIT'] == 1:
        if session['REVERSE'] == 1:
            session['PLAYERTURN'] += 1
            if session['PLAYERTURN'] == session['NUMPLAYERS']:
                session['PLAYERTURN'] = 0
            session['WAIT'] -= 1
        elif session['REVERSE'] == -1:
            session['PLAYERTURN'] -= 1
            if session['PLAYERTURN'] < 0:
                session['PLAYERTURN'] = int(session['NUMPLAYERS'] - 1)
            session['WAIT'] -= 1
    if session['WAIT'] == 2:
        if session['REVERSE'] == 1:
            session['PLAYERTURN'] += 1
            if session['PLAYERTURN'] == session['NUMPLAYERS']:
                session['PLAYERTURN'] = 0
            session['WAIT'] -= 2
        elif session['REVERSE'] == -1:
            session['PLAYERTURN'] -= 1
            if session['PLAYERTURN'] < 0:
                session['PLAYERTURN'] = int(session['NUMPLAYERS'] - 1)
            session['WAIT'] -= 2

    # Check for Uno after ending the turn
    if session.get('unoPlayer') is not None and len(session['PLAYERS'][session.get('unoPlayer')]) == 1:
        # Redirect to the Uno route to penalize the player
        return redirect('/uno')

    # Check if the current player won or the Uno status should be activated
    if checkWinner():
        return redirect('/win')

    session.modified = True

    return redirect('/nextturn')


@app.route('/win')
def win():
    return render_template('win.html', winner=session['WINNER'], playername=session['PLAYERNAME'], turns=session['visits'])


@app.route('/nextturn')
def nextturn():
    return render_template('nextturn.html',drawbutton=session['DRAWBUTTON'], pickbutton=session['PICKBUTTON'],
                                   endbutton=session['ENDBUTTON'],uno_pending=session['UNO_PENDING'], playable=session['PLAYABLE'],
                                   players=session['PLAYERS'],
                                   currentPlayer=session['PLAYERTURN'], numPlayers=session['NUMPLAYERS'],
                                   discards=session['DISCARDS'], wildcard=session['WILDCARD'],
                                   drawfour=session['DRAWFOUR'], playername=session['PLAYERNAME'],
                                   wait=session['WAIT'], reverse=session['REVERSE'], drawcards=session['DRAWCARDS'])


@app.route('/WILDCARD/<card>')
def wildcard(card):
    session['DISCARDS'].insert(0, card)
    session['WILDCARD'] = False
    session.modified = True
    return redirect('/board')


@app.route('/DRAWFOUR/<card>')
def drawfour(card):
    session['DISCARDS'].insert(0, card)
    session['DRAWFOUR'] = False
    session.modified = True
    return redirect('/board')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='5118', debug=True)
