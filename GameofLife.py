import random

# Welcome Message and Directions
print('Welcome to the Game of Life - Single Player Version\n'
      'Directions:\n'
      '1. Design your character\n'
      '2. Choose your education path...\n'
      '3. Roll the dice and see how your life unfolds!')

# Character Profile
print('\nDesign your Character')
name = input('Please enter your name: ')
print(f'Your name is {name}, your initial wealth is $1000.')
print("Let's begin!")
player_profile = ''
def update_player_profile():
    global player_profile
    player_profile = (
        f"Player Profile\n"
        f"Name: {name}\n"
        f"Marital Status: {marital_status}\n"
        f"Spouse: {spouse if spouse else 'None'}\n"
        f"Children: {', '.join(children_names) if children_names else 'None'}\n"
        f"Education: {education}\n"
        f"Career: {career}\n"
        f"Salary: ${salary}\n"
        f"Bank Balance: ${bank_balance}\n"
        f"Loans: ${loans}\n"
        f"Properties: {', '.join(property_name) if property_name else 'None'}\n"
        f"Property Value: ${property_value}\n"
    )
    return player_profile

# Profile Variables
#strings
education = ''
career = ''
marital_status = 'Unmarried'
spouse = ''
#integers
bank_balance = 1000
loans = 0
salary = 0
property_value = 0
children = 0
#lists
property_name = []
children_names = []

# Game Variables
#integers
position = 0
roll = 0

#tuples
properties = ('Malibu Mansion', 'Reno Ranch', 'Vicksburg Villa', 
             'Atlanta Apartment', 'Huntsville Home', 'Cleveland Cottage')
property_price = (400000, 80000, 200000, 300000, 100000, 80000)
non_degree_careers = ('Athlete', 'Police Officer', 'Mechanic', 'Hair Stylist', 'Salesperson')
non_degree_salary = (60000, 40000, 30000, 30000, 20000)
degree_careers = ('Teacher', 'Programmer', 'Lawyer', 'Doctor', 'Accountant')
degree_salary = (50000, 70000, 90000, 100000, 70000)

# Gameplay Functions

#
def roll_dice():
    return random.randint(1, 6)

#
def player_roll():
    player_rolls = input('Press "Enter" to roll the dice: ')
    if player_rolls == '':
        roll = roll_dice()
        print(f'You rolled a {roll}')
        return roll
    else:
        print("You didn't press Enter. Try again!")
        return player_roll()
#If they have enough funds, the player may buy a property
def buy_a_house():
    global property_value, property_name, bank_balance
    #inform the player where they have landed
    print('You landed on Buy a House!')
    #ask the player if they would like to buy a house 
    buy = input('Would you like to buy a house? \nEnter Y (yes) or N (no): ')
    cont = 'y'
    while cont.lower() == 'y':
        if buy.lower() == 'y':
            print('Roll the dice to tour three properties.')
            roll = player_roll()
            #chose a property
            if roll <= 3:
                print(f"Here are the properties you can choose from: {properties[:3]}")
                choice = None
                while choice not in range(1, 4):
                    try:
                        choice = int(input('Enter a number 1-3 to choose your property: '))
                        if choice not in range(1, 4):
                            print('Please enter a valid choice - 1, 2, or 3.')
                    except ValueError:
                        print('Invalid input. Please enter a number between 1 and 3.')
                if choice in range(1, 4):
                    #check if the player has enough money to buy the property
                    if bank_balance >= property_price[choice - 1]:
                        chosen_prop = properties[choice - 1]
                        property_name.append(chosen_prop)
                        val = property_price[choice - 1]
                        property_value += val
                        bank_balance -= val
                        print(f'You chose {chosen_prop}, worth ${val}. Your current bank balance is ${bank_balance}.')
                        cont = 'n'
                        #save the players choices
                        return property_name, property_value, bank_balance
                    else:
                        #if the player does not have enough money, let them know
                        chosen_prop = properties[choice - 1]
                        print(f'You do not have enough savings to buy {chosen_prop}.')
                        cont = input('Would you like to tour a different property? Enter Y (yes) or N (no; exit): ')
                        if cont.lower() != 'y':  
                            print("You chose not to buy a house. Your current bank balance is ${bank_balance}.")
                            return None
                        else:
                            continue
            
            else:
                print(f"Here are the properties you can choose from: {properties[3:]}")
                choice = None
                while choice not in range(1, 4):
                    try:
                        choice = int(input('Enter a number 1-3 to choose your property: '))
                        if choice not in range(1, 4):
                            print('Please enter a valid choice - 1, 2, or 3.')
                    except ValueError:
                        print('Invalid input. Please enter a number between 1 and 3.')
                if choice in range(1, 4):
                    if bank_balance >= property_price[choice + 2]:
                        chosen_prop = properties[choice + 2]
                        property_name.append(chosen_prop)
                        val = property_price[choice + 2]
                        property_value += val
                        bank_balance -= val
                        print(f'You chose {chosen_prop}, worth ${val}. Your current bank balance is ${bank_balance}.')
                        cont = 'n'
                        #save the players choices
                        return property_name, property_value, bank_balance
                    else:
                        #if the player does not have enough money, let them know
                        chosen_prop = properties[choice + 2]
                        print(f'You do not have enough savings to buy {chosen_prop}.')
                        cont = input('Would you like to tour a different property? Enter Y (yes) or N (no; exit): ')
                        if cont.lower() != 'y':
                            print("You chose not to buy a house.")
                            return None
                        else:
                            continue
                else:
                    print('Please enter a valid choice - 1, 2, or 3.')
                    continue
        elif buy.lower() == 'n':
            #the player chose not to buy a house due to lack of funds
            print('You chose not to buy a house.')
            cont = 'n'
            return None
    
        else:
            #the player chose not to buy a house
            print('Please enter Y (yes) or N (no).')
            continue

#Player encounters an unexpected event       
def unexpected_event():
    #define global variables
    global bank_balance
    #inform player where they have landed
    print('You landed on a Unexpected Event!\nRoll the dice to get an event.')
    #player rolls the dice
    roll = player_roll()
    #based on roll, determine the event type
    if roll == 1:
        #inform player of event and cost/gain
        print('The Stock Market crashes! You lost $2000.')
        #update bank account balance
        bank_balance -= 2000
    elif roll == 2:
        print('You got in a car accident! You pay $500.')
        bank_balance -= 500
    elif roll == 3:
        print('You won a local art competition and sold your piece for $600.')
        bank_balance += 600
    elif roll == 4:
        print('Your great aunt, three times removed,passed away and left her'
              'designer collection to you! The collection is worth $4000.')
        bank_balance += 4000
    elif roll == 5:
        print('Your floor has termites, call pest control! You pay $1000.')
        bank_balance -= 1000
    elif roll == 6:
        print('You got fined $50 for throwing tomatoes in the market square.')
        bank_balance -= 50
    #return bank balance
    return bank_balance
    
#Player wins the lottery
def win_lottery():
    #define global variable(s)
    global bank_balance
    #inform player where they have landed
    print('You landed on Win the Lottery!\nRoll the dice to enter the lottery.')
    #player rolls the dice
    roll = player_roll()
    if roll == 1:
        #display winning to player
        print('You won $100!')
        #add winnings to bank account balance
        bank_balance += 100
    elif roll == 2:
        print('You won $100!')
        bank_balance += 100
    elif roll == 3:
        print('You won $200!')
        bank_balance += 200
    elif roll == 4:
        print('You won $300!')
        bank_balance += 300
    elif roll == 5:
        print('You won $500!')
        bank_balance += 500
    elif roll == 6:
        print('You won $1000!')
        bank_balance += 1000
        
    print(f'Your current account balance is {bank_balance}')
    return bank_balance
    
#Player goes on a vacation 
def family_vacation():
    #define global variable(s)
    global bank_balance
    #inform player where they have landed
    print('You landed on Family Vacation!\nRoll the dice to see where your going.')
    #player rols dice
    roll = player_roll()
    #determine the vacation type
    if roll in range(1,3):
        #inform player of vacation and cost
        print('You talke a road trip to Yosemite and go camping! Pay $200.')
        #update bank account balance
        bank_balance -= 200
    if roll in range(3,5):
        print('You fly to San Juan, Puerto Rico! Pay $500.')
        bank_balance -= 500        
    if roll in range(4,7):
        print('You fly to Accra, Ghana! Pay $1000.')
        bank_balance -= 100      
    #display balance to player
    print(f'Your current account balance is {bank_balance}')
    #return balance
    return bank_balance

#Player has a baby
def have_baby():
    global children_names, bank_balance, children
    #inform the player where they have landed
    print('You landed on Have a Baby!\nWould you like to have a baby?')
    #ask if the player would like to have a baby
    cont = input('Enter Y (yes) or N (no): ')
    if cont.lower() == 'y':
        print('Roll the dice for a new addition to your family!')
        roll = player_roll()
        if roll in range(1,3):
            #inform player of the birth of their child, and associated costs
            print('Congratulations, you had a baby boy. You paid $50 in hospital bills.')
            #allow player to name the child
            name = input('Enter his name on the birth certificate: ')
            #save the childs name to a list
            children_names.append(name)
            #keep count of how many children the player has
            children += 1
            #subtract hospital costs
            bank_balance -= 50
        if roll in range(3,5):
            print('Congratulations, you had a baby girl. You paid $50 in hospital bills.')
            name = input('Enter her name on the birth certificate: ')
            children_names.append(name)
            children += 1
            bank_balance -= 50
        if roll == 5:
            print('Congratulations, you had twins. You paid $100 in hospital bills.')
            name = input("Enter the first baby's name on the birth certificate: ")
            children_names.append(name)
            name = input("Enter the second baby's name on the birth certificate: ")
            children_names.append(name)
            children += 2
            bank_balance -= 100
        if roll == 6:
            print('Congratulations, you had triplets. You paid $150 in hospital bills.')
            name = input("Enter the first baby's name on the birth certificate: ")
            children_names.append(name)
            name = input("Enter the second baby's name on the birth certificate: ")
            children_names.append(name)
            name = input("Enter the third baby's name on the birth certificate: ")
            children_names.append(name)
            children += 3
            bank_balance -= 150
    elif cont.lower() == 'n':
        print('You chose not the have a baby.')
        return
    else:
        print('Invalid input, please try again.')
        have_baby()
    #return childs name, the number of children, and the bank account balance
    return children_names, children, bank_balance

#Player gets an education
def education_path():
    global position, education,loan
    #ask the player which educational path they would like to take
    choice = input('Would you like to go to university?\nEnter Y (yes) or N (no): ')
    if choice.lower() == 'y':
        #if yes, take out a loan and start at space 0
        print('You have chosen to go to university. You took out a loan of $40000'
              '\nYou will start your journey at position one.') 
        position = 1
        #change the players education to university educated
        education = 'University Degree'
        loans = 40000
        return position, education, loans
    elif choice.lower() == 'n':
        print('You have chosen not to go to university. \nYou will start your journey at position ten.') 
        position = 10
        education = 'High School Diploma'
        return position, education   
    else:
        print('Invalid input, please try again.')
        education_path()
        
#Player gets a career
def career_path():
    global career, salary
    #inform the player where they have landed
    print('STOP! Its time to choose a career.\nRoll the dice to see your options.')
    roll = player_roll()#just for the illusion of game play - the roll doesnt affect the career options
    if education == 'University Degree':
        random_indexes = random.sample(range(len(degree_careers)), 3) #random career indexes
        options = [degree_careers[i] for i in random_indexes]  #career options
        print(f'You may choose from the following careers:\n1. {options[0]}\n2. {options[1]}\n3. {options[2]}')
        choice = None
        while choice not in [1, 2, 3]:  #ensure valid input
            try:
                choice = int(input('Enter a number 1-3 to select your career path: '))
                if choice not in [1, 2, 3]:
                    print('Invalid input. Please select 1, 2, or 3.')
            except ValueError:
                print('Invalid input. Please enter a number.')

        career = options[choice - 1]  #save their career choice
        salary = degree_salary[degree_careers.index(career)]  #save the corresponding starting salary
        print(f'You chose {career}, which has a starting salary of ${salary}.')
        return career, salary
    
    else:
        random_indexes = random.sample(range(len(non_degree_careers)), 3) #random career indexes
        options = [non_degree_careers[i] for i in random_indexes]  #career options
        print(f'You may choose from the following careers:\n1. {options[0]}\n2. {options[1]}\n3. {options[2]}')
        choice = None
        while choice not in [1, 2, 3]:  #ensure valid input
            try:
                choice = int(input('Enter a number 1-3 to select your career path: '))
                if choice not in [1, 2, 3]:
                    print('Invalid input. Please select 1, 2, or 3.')
            except ValueError:
                print('Invalid input. Please enter a number.')

        career = options[choice - 1]  #save their career choice
        salary = non_degree_salary[non_degree_careers.index(career)]  #save the corresponding starting salary
        print(f'You chose {career}, which has a starting salary of ${salary}.')
        return career, salary

#Player gets a promotion
def promotion():
    global salary
    #inform the user where they have landed
    print('Congratulations, you landed on a Promotion!\nYour salary has increased by 10%.')
    #increase salary by 10%
    salary = salary * 1.1
    #return new salary
    return salary
#Payday
def pay_day():
    global bank_balance
    print(f'You landed on a Pay Day! Collect your salary of ${salary}')
    bank_balance += salary
    print(f'After this pay day, your current account balance is ${bank_balance}')

def career_swap():
    global career, salary
    #inform the player where they have landed
    print('You landed on Career Swap!')
    cont = input('Would you like to swap careers, enter Y (yes) or N (no): ')
    while cont.lower() == 'y':
        print('Roll the dice to get career options.')
        roll = player_roll()#just for the illusion of game play - the roll doesnt affect the career options
        if education == 'University Degree':
            random_indexes = random.sample(range(len(degree_careers)), 3) #random career indexes
            options = [degree_careers[i] for i in random_indexes]  #career options
            print(f'You may choose from the following careers:\n1. {options[0]}\n2. {options[1]}\n3. {options[2]}')
            choice = None
            while choice not in [1, 2, 3]:  #ensure valid input
                try:
                    choice = int(input('Enter a number 1-3 to select your career path: '))
                    if choice not in [1, 2, 3]:
                        print('Invalid input. Please select 1, 2, or 3.')
                except ValueError:
                    print('Invalid input. Please enter a number.')
            career = options[choice - 1]  #save their career choice
            salary = degree_salary[degree_careers.index(career)]  #save the corresponding starting salary
            print(f'You chose {career}, which has a starting salary of ${salary}.')
            return career, salary
        else:
            random_indexes = random.sample(range(len(non_degree_careers)), 3) #random career indexes
            options = [non_degree_careers[i] for i in random_indexes]  #career options
            print(f'You may choose from the following careers:\n1. {options[0]} - \n2. {options[1]}\n3. {options[2]}')
            choice = None
            while choice not in [1, 2, 3]:  #ensure valid input
                try:
                    choice = int(input('Enter a number 1-3 to select your career path: '))
                    if choice not in [1, 2, 3]:
                        print('Invalid input. Please select 1, 2, or 3.')
                except ValueError:
                    print('Invalid input. Please enter a number.')
            career = options[choice - 1]  #save their career choice
            salary = non_degree_salary[non_degree_careers.index(career)]  #save the corresponding starting salary
            print(f'You chose {career}, which has a starting salary of ${salary}.')
            return career, salary
    if cont.lower() == 'n':
            print(f'You have chosen to keep your current career as a{career}')
            return None
    else:
        print('Invalid input, please try again')
        career_swap()
            
#player gets married
def wedding():
    #define global variables
    global marital_status, spouse, bank_balance, name
    #ask the player if they would like to get married
    print('STOP. Would you like to get married?')
    #inform the player of the cost
    print('The marriage license costs $60, and your wedding costs $300.')
    cont = input('Enter Y (yes) or N (no): ')
    if cont.lower() == 'y':
        #allow to player to enter the name of their spouse
        spouse = input('Enter the name of your spouse: ')
        #subtract cost of marriage
        bank_balance -= 360
        #adjust marrige status in player profile
        marital_status = 'Married'
        #display a congratulatory message to the player
        print(f'Congratulations {name}, you are now married to {spouse}')
        #return new global variable values
        return marital_status, spouse, bank_balance
    elif cont.lower() == 'n':
        #Player chooses not to get married and exits
        print('You have chosen not to get married.')
        return None
    else:
        #player doesnt enter y or n
        print('Invalid input, please try again.')
        wedding()

#function position call tuples
univ = (1,)
car_choi = (10,)
get_married = (20,)
payday = (10,18, 26, 34, 42, 50, 58, 66, 74, 82, 90, 98)
unexp_event = (12, 22, 46, 70, 75)
fam_vacay = (23, 37, 51, 64, 80, 94)
have_a_baby = (25, 32, 36, 44, 47)
buy_house = (30, 40, 45, 52, 60, 84)
job_promo = (21, 41, 61, 71, 77, 81, 91)
lottery = (39, 43, 72, 86, 99)
car_swap = (49,73)

retire = (100,)

#Mandatory fields: Career choice, get married, retirement, if the user does not land on these fields based on their position,
# they will not be allowed to pass until they are True. This will force the user to land on these fields

mandatory_fields = [False, False, False]
#keep track of if the player has passed a payday
pay_days = [False, False, False, False, False, False, False, False, False, False, False, False]

#GAMEPLAY STARTS HERE
position = 1

while position < 100:
    
    if position in univ:
        education_path()
    elif position in car_choi:
        career_path()
    elif position in get_married:
        wedding()
    elif position in payday:
        pay_day()
    elif position in unexp_event:
        unexpected_event()
    elif position in fam_vacay:
        family_vacation()
    elif position in have_a_baby:
        have_baby()
    elif position in buy_house:
        buy_a_house()
    elif position in job_promo:
        promotion()
    elif position in lottery:
        win_lottery()
    elif position in car_swap:
        career_swap()
    else:
        print('You landed on a empty space, roll again.')
    index = pay_days.index(False)
    if position > payday[index-1]:
        print(f'You passed a pay day, your salary of ${salary} has been deposited to your account!')
        bank_balance += salary
        pay_days
    position += player_roll()
player_profile = player_profile()
print(player_profile)

