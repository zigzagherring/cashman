# bot.py
import os
import locale
import discord
import time
import uuid
import pandas as pd
import re
#from dotenv import load_dotenv

#Setup global variables here
#load_dotenv()
client = discord.Client()
TOKEN = 'NzI4MjkxNTI3MTA0NzkwNTI4.Xv4izw.KQndfQkN7NAFyIuYy-Ve81jbx1M'
ChanTotal = 0
totalFilePath = r'C:\Users\brand\source\repos\cashman\cashman\total'
transFilePath = r'C:\Users\brand\source\repos\cashman\cashman\transactions'
totals = {}
transactions = list()
transFields = list()
PCs = {
    'bscbeg#4160':'DM',
    'Chris.Levy#3531':'Byrn',
    'galzra#0174':"Vern",
    'Erin#9336': 'Kelsee',
    'Alyuwe#6152': 'Fin',
    'Lennessy#1214': 'Dax'
    }
#Setup non-async here
#setup totals dictionary (key is channel name, value is total)
f = open(totalFilePath, 'r')

for line in f:
    totals[line.split('|')[0].strip()] = int(line.split('|')[1].strip())
f.close()

def getTotalRecords():
    global totals
    totList = list()

    for tot in totals:
        totList.append(tot+'|'+str(totals[tot]))

    return totList

def writeTotals():
    global totals    
    f = open(totalFilePath,'w')
    totRecords = getTotalRecords()
    
    f.seek(0)
    
    print('Preparing to write totals...')
    for line in totRecords:
        f.write(line)
        f.write('\n')
        print('Writing line: <'+line+'>')
    
    f.close()

    print('Totals written...')

class transaction:
    def __init__(self, message):
        self.origContent = str(message.content)
        self.content = ' '.join(self.origContent.split()) #This will remove all multiple white space
        self.guild = str(message.guild)
        self.channel = str(message.channel)
        self.user = str(message.author)
        try: 
            self.PC = PCs[str(message.author)]
        except:
            self.PC = 'Unknown'
        self.time = time.time()

        #Let's figure out what type of transaction this is
        if self.content[0] == '+':
            self.type = '+'
            self.content = self.content[1:].lstrip() #remove the + and any new leading white space
        elif self.content[0:1].upper() == 'CR':
            self.type = '+'
            self.content = self.content[2:].lstrip() #remove the CR and any new leading white space
        elif self.content[0].isdigit():
            self.type = '+'
            #Nothing to trim here
        elif message.content[0] == '-':
            self.type = '-'
            self.content = self.content[1:].lstrip() #remove the - and any new leading white space
        elif str(message.content).split(' ')[0].lower() == 'report':
            self.type = 'report'
            reportCmd = str(message.content).split(' ')

            self.reportNum = 0
            self.reportType = 'a'
            self.reportUser = 'a'
            
            if len(reportCmd) > 1:
                self.reportNum = int(reportCmd[1])
            if len(reportCmd) > 2:
                self.reportType = reportCmd[2]
            if len(reportCmd) > 3:
                self.reportUser = reportCmd[3]
        elif str(message.content).split(' ')[0].lower() == 'listpc':    
            self.type = 'listPC'
          
        else:
            self.type = 'other'
        
        
        #We only want to fill out our data if its a deposit or withdrawal.  Otherwise, its a service command.
        if self.type != 'other':
            #Now lets establish who is giving commands.  If we cant find the author name in our PC lookup, then let's just put it down as unknown.  We can fix later.
            
            self.tempContent = self.content.replace(',','')
            self.exitFlag = 0
            self.amtHelp = ''
            self.ctr = 0

            while self.exitFlag == 0 and self.ctr < len(self.content):
                if self.content[self.ctr].isdigit():
                    self.amtHelp = self.amtHelp + self.content[self.ctr]                

                if self.content[self.ctr] == ' ':
                    self.exitFlag = 1

                self.ctr = self.ctr + 1
            
            try:
                self.amount = int(self.amtHelp)
            except:
                self.amount = 0

            self.content = self.content[self.content.find(' '):]   

            self.ID = 0

            #Now let's extract the comment, if any
            if self.content.find('#') != -1:
                #This means we found a comment
                self.comment = self.content[self.content.find('#')+1:]
                #Now let's delete it from content
                self.content.replace('#'+self.comment,'')
            else:
                self.comment = ''
            
            self.record = '|'.join((str(self.ID), str(self.time), self.guild, self.channel, self.user, self.PC, self.type, str(self.amount), self.comment, self.origContent))
            self.recordList = ((str(self.ID), str(self.time), self.guild, self.channel, self.user, self.PC, self.type, str(self.amount), self.comment, self.origContent))
    
    def write(self):
        global transactions
        print('Creating transaction record:')
        print(self.record)
        f = open(transFilePath,'a')
        f.write('\n')
        f.write(self.record)        
        f.close()

        i = 0
        transactions.append({})
        for item in self.recordList:            
            print("Trans dict is currently: "+str(transFields[i]))
            transactions[len(transactions)-1][transFields[i]]=item
            i = i + 1
        print('Added transaction to listdict:')
        print(transactions[len(transactions)-1])



    

def currentTotal(channel):
    global totals    
    try: 
        msg = "Current total is: " + '{:,}'.format(totals[channel])
    except KeyError:
        msg = "Current total is not yet initialized."
    print(msg)
    return msg

def checkTotal(channel):
    global totals

    if channel not in totals.keys():
        totals[channel] = 0
        return -1

    return 0


#Setup async functions here
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    global totals 
    global transactions
    global PCs
    
    if str(message.author) != "cashman#3230":
        #Let's not respond to our own messages
        if message.channel.name[0:2] == "cm":
            #Make sure we are only processing messages from a cashman channel 
            print("Input received on the right channel")
            
            currMsg = transaction(message)            

            #Lets log some stuff to the console for debug
            currentTotal(currMsg.channel)
            print(currMsg.user + ' @ ' + currMsg.channel + ' : ' + currMsg.origContent)
            
            
            #Check to see if we were given instructions
            if currMsg.type =='+':                                
                #Let's add to our total
                print("Adding to total: " + '{:,}'.format(currMsg.amount))
                checkTotal(currMsg.channel)
                totals[currMsg.channel] = totals[currMsg.channel] + currMsg.amount
                writeTotals()
                currMsg.write()
                await message.channel.send(currentTotal(currMsg.channel))
            
            elif currMsg.type == "-":                
                #Let's decrement from total
                #First, we check for errors
                if currMsg.amount > totals[str(message.channel)]:
                    print("Error, withdrawal amount too high, taking no action")
                    await message.channel.send("**ERROR: __withdrawal amount too high__!**")
                    await message.channel.send(currentTotal(currMsg.channel))                
                else:
                    print("Subtracting from total: " + '{:,}'.format(currMsg.amount))
                    checkTotal(currMsg.channel)
                    totals[currMsg.channel] = totals[currMsg.channel] - currMsg.amount
                    writeTotals()
                    currMsg.write()
                    await message.channel.send(currentTotal(currMsg.channel))

            elif message.content[0] == "=":
                #Let's return our total to the channel
                await message.channel.send(currentTotal(currMsg.channel))
            
            elif currMsg.type == 'report':
                recordCount = 0
                if currMsg.reportNum == 0:
                    reportShorten = len(transactions)
                else:
                    reportShorten = currMsg.reportNum
                    # Num -> Type -> User
                for line in transactions[len(transactions)-reportShorten:]:
                    if line['channel'] == currMsg.channel and line['guild'] == currMsg.guild:
                        if line['type'].lower() == currMsg.reportType.lower() or currMsg.reportType.lower() == 'a':
                            if line['PC'].lower() == currMsg.reportUser.lower() or currMsg.reportUser.lower() == 'a':
                                recordCount = recordCount + 1
                            
                                if line['type'] == '+':
                                    thisType = '*deposited* by '
                                else:
                                    thisType = '_withdrawn_ by '
                    
                                print(line['amount'])
                                thisReport = ''
                                thisReport = '```CR '+'{:10,}'.format(int(line['amount']))+' '
                                thisReport = thisReport + thisType + line['PC'] 
                                thisReport = thisReport + ' for '
                    
                                if line['comment'] == '':
                                    thisReport = thisReport + 'no reason'
                                else:
                                    thisReport = thisReport + line['comment']
                    
                                thisReport = thisReport +'```'                    
                                await message.channel.send(thisReport)                    
                                thisReport = ''
                await message.channel.send('Returned '+str(recordCount)+' records.')  
                

            elif currMsg.type == 'listPC':
                for PC in PCs:
                    await message.channel.send('User: __'+PC+'__ is **'+PCs[PC]+'**')                    

            else:
                if str(message.content).strip() != "help":
                    print('Unrecognized input')
                    await message.channel.send('**ERROR: __unrecognized input__, please see usage information below.**')

                await message.channel.send("**__Deposits__** - Either start your line with a '+' or simply type in the amount of the deposit.")
                await message.channel.send("**__Withdrawals__** - Start your line with a '-'.")
                await message.channel.send("**__Account Balance__** - Just type '=' to get the current account balance.")
                await message.channel.send("**__Transaction Comments__** - You can add comments to your transaction using the '#' symbol.  Everything after that symbol will be treated as a comment.")   
                await message.channel.send("**__Reports__** - syntact is 'report Number Type User'.")
                await message.channel.send("    **Number** is the number of records you want to return.  Set number to 0 to return all records (this may take a while!). Omitting Number returns all records by default.")  
                await message.channel.send("    **Type** is either '+' for deposits, '-' for withdrawals, or 'a' for everything.  Omitting Type returns all types by default.")
                await message.channel.send("    **User** is the last name of the PC.  Omitting this returns data for all PCs.")
                await message.channel.send("**__ListPC__** - the command 'listpc' will list all PC names for use in the 'report' function.")
                
#Get totals by channel
f = open(totalFilePath, 'r')
for line in f:
    totals[line.split('|')[0].strip()] = int(line.split('|')[1].strip())
f.close()

f = open(transFilePath, 'r')
ctr = 0
i = 0

for line in f:
    line = ' '.join(line.split())
    print('Segmented line:')     
    splitLine = line.split('|')
    print(splitLine)

    if ctr == 0:
        for item in splitLine:
            transFields.append(item)

    else:
        transactions.append({})
        for item in splitLine:
            print("Ctr-1 = "+str(ctr-1))
            print("Trans dict is currently: "+str(transFields[i]))
            transactions[ctr-1][transFields[i]]=item
            i = i + 1

    ctr = ctr + 1
    i=0       
f.close()

print(transactions)

client.run(TOKEN)


