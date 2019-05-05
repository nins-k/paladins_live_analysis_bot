# Work with Python 3.6
import discord
import requests
import hashlib
from datetime import datetime as dt
import pandas as pd
import os



class PaladinsClient:
    
    
    def __init__(self, dev_id, auth_key):
        
        self.dev_id = dev_id
        self.auth_key = auth_key
        
        self.base_endpoint = "http://api.paladins.com/paladinsapi.svc"
        self.response_format = "Json"
        
        self.session_id = None


    def getTimeStamp(self):
        
        # Returns current UTC time in yyyyMMddHHmmss format
        
        return dt.utcnow().strftime("%Y%m%d%H%M%S")


    def createSignature(self, method_name, time_stamp):
        
        # Returns hashed concatenated string
        sig_string = self.dev_id + method_name + self.auth_key + time_stamp

        return hashlib.md5(sig_string.encode()).hexdigest()

   
    def createSession(self):
        
        # Create a new session
        # Returns session object (json) and session id
        # /createsession[ResponseFormat]/{developerId}/{signature}/{timestamp}

        method_name = "createsession"
        time_stamp = self.getTimeStamp()
        signature = self.createSignature(method_name, time_stamp)
        api_url = self.base_endpoint + "/{}{}/{}/{}/{}".format(method_name, self.response_format, 
                                              self.dev_id, signature, time_stamp)
        json = requests.get(api_url).json()
        
        self.session_id = json['session_id']


    def getActiveSessionId(self):

        if not self.testSession():
            self.createSession()

        return self.session_id


    def testSession(self):
        
        # Test if a session is active
        # Returns boolean
        # /testsession[ResponseFormat]/{developerId}/{signature}/{session}/{timestamp}
    
        session_id = self.session_id
        method_name = "testsession"
        time_stamp = self.getTimeStamp()
        signature = self.createSignature(method_name, time_stamp)
        api_url = self.base_endpoint + "/{}{}/{}/{}/{}/{}".format(method_name, self.response_format, 
                                                             self.dev_id, signature, 
                                                             session_id, time_stamp)
        response = requests.get(api_url)

        return response.text.startswith("\"This was a successful test")

    
    def getApiUrl(self, method_name, player_id=None, match_id=None, queue_id=None):
        
        session_id = self.getActiveSessionId()
        time_stamp = self.getTimeStamp()
        signature = self.createSignature(method_name, time_stamp)
        id_ = player_id if player_id != None else match_id
        
        api_url = self.base_endpoint + "/{}{}/{}/{}/{}/{}/{}".format(method_name, self.response_format, 
                                                                self.dev_id, signature,
                                                                session_id, time_stamp,
                                                                id_)
        if queue_id != None:
            api_url += "/{}".format(queue_id)
  
        return api_url


    def getPlayer(self, player_id):
        
        api_url = self.getApiUrl('getplayer', player_id=player_id)
        response = requests.get(api_url)

        return pd.read_json(response.text)


    def getMatchDetails(self, match_id):
        
        # Get match details
        # /getmatchdetails[ResponseFormat]/{developerId}/{signature}/{session}/{timestamp}/{match_id}
    
        api_url = self.getApiUrl('getmatchdetails', match_id=match_id)
        response = requests.get(api_url)
        
        return pd.read_json(response.text)

    
    
    def getQueueStats(self, player_id, queue_id):
        
        api_url = self.getApiUrl('getqueuestats', player_id=player_id, queue_id=queue_id)
        response = requests.get(api_url)

        return pd.read_json(response.text)
    
    
    def getChampionRanks(self, player_id):
        
        api_url = self.getApiUrl('getchampionranks', player_id=player_id)
        response = requests.get(api_url)
        
        return pd.read_json(response.text)
        
        
    def getMatchPlayerDetails(self, match_id):
        
    
        api_url = self.getApiUrl('getmatchplayerdetails', match_id=match_id)
        response = requests.get(api_url)
        
        return pd.read_json(response.text)
    
    
    def getPlayerStatus(self, player_id):
        
        api_url = self.getApiUrl('getplayerstatus', player_id=player_id)
        response = requests.get(api_url)
        
        return pd.read_json(response.text)
    
    
    def getMatchHistory(self, player_id):
        
        api_url = self.getApiUrl('getmatchhistory', player_id=player_id)
        response = requests.get(api_url)
        
        return pd.read_json(response.text)
    
    
    def getAllData(self, player_info, queue_id):
        
        df = pd.DataFrame(columns=['Player', 'Champion', 'CKDA', 'CMat', 'OKDA', 'KDAR', 'Win%'])
        
        for i in range(len(player_info)):
            try:
                player_name = player_info.iloc[i].playerName
                print("Getting data for player {}".format(player_name))
                champion_name = player_info.iloc[i].ChampionName
                # print(i, player_name, champion_name)
                champion_data = self.getChampionRanks(player_id=player_name)
				
                # Calculate KDA for all champions
                kda = (champion_data['Kills'] + 0.5*champion_data['Assists'])/champion_data['Deaths']
				
                # Append KDA column
                champion_data['kda'] = kda
				
                # Calculate overall KDA across all champions
                overall_kda= round((sum(champion_data['Kills'])+0.5*sum(champion_data['Assists']))/sum(champion_data['Deaths']), 2)

                # Calculate KDA for the current champion
                champion_row = champion_data.loc[champion_data['champion'] == champion_name]
                champion_kda = (champion_row['Kills'] + 0.5*champion_row['Assists'])/champion_row['Deaths']
                champion_kda = round(champion_kda.iloc[0], 2)

                # Get KDA rank of current champion for the player
                champion_data = champion_data.sort_values(['kda'], ascending=[0])
                champions = list(champion_data['champion'])
                kda_rank = champions.index(champion_name) + 1
				
                # Get matches played and win rate of the current champion for the player
                champion_matches = champion_row['Wins'] + champion_row['Losses']
                champion_matches = champion_matches.iloc[0]
				
                win_rate = champion_row['Wins']/(champion_row['Wins'] + champion_row['Losses'])
                win_rate = str(round(100*win_rate.iloc[0], 0)) + "%"
				
                df.loc[i] = [player_name, champion_name, champion_kda, champion_matches, overall_kda, kda_rank, win_rate]
            except:
                    continue
					
        df = df.sort_values(['CKDA'], ascending=[0]) 
            
        return df

    def getMatchHistory(self, player_id):
        
        api_url = self.getApiUrl('getmatchhistory', player_id=player_id)
        response = requests.get(api_url)
        
        return pd.read_json(response.text)
    
    def getWinRate(self, player_id, last_matches_count=50):
        
        history_data = self.getMatchHistory(player_id=player_id)
        selected_data = history_data.iloc[:last_matches_count,:]

        return sum(selected_data.Win_Status=='Win'), selected_data.shape[0]

    def getLastMatchData(self, player_id):

        def getKDAString(row):
            return "{}/{}/{}".format(row['Kills_Player'], row['Deaths'], row['Assists'])
            
        history_data = self.getMatchHistory(player_id=player_id)
        last_match_id = (history_data['Match'])[0]
        match_data = self.getMatchDetails(last_match_id)
        
        match_data['KDA'] = match_data.apply(lambda row: getKDAString(row), axis=1)

        player_row = match_data.loc[match_data['playerName'] == player_id]
        match_data.loc[match_data['playerName'] == player_id, 'Reference_Name'] = "*" + player_row['Reference_Name']
        
        required_data = match_data.sort_values('Win_Status', ascending=False)[[
            'playerName', 'Reference_Name', 'Damage_Player', 'Damage_Taken', \
            'Damage_Mitigated', 'Healing', 'KDA', 'PartyId']]
        
        u = sorted(required_data.PartyId.unique())
        map_dict = {}
        for index, i in enumerate(u):
            map_dict.update({i : "Party {}".format(index + 1)})
        required_data['PartyId'] = required_data['PartyId'].map(map_dict)
        
        required_data = required_data.transpose()

        return required_data

    
    def getCurrent(self, player_id):
        
        player_status = self.getPlayerStatus(player_id)
        if player_status['status'][0] != 3:
            return None
        else:
            live_match_id = player_status['Match'][0]
            data = self.getMatchPlayerDetails(live_match_id)
            
            player_info = data.sort_values('taskForce')[['ChampionName', 'playerName']]
            team1_info = player_info[:5]
            team2_info = player_info[5:]
            queue_id = data['Queue'][0]
            
            team1_data = self.getAllData(team1_info, queue_id)
            team2_data = self.getAllData(team2_info, queue_id)
            
            # total_data = team1_data.append(team2_data)
            
            return team1_data, team2_data
        

    def saveMatchToCsv(self, match_data):
        
        match_data.to_csv("{}.csv".format((self.getTimeStamp())))
    
	
# TOKEN = os.environ['TOKEN']

# client = discord.Client()
# dev_id = str(os.environ['dev_id'])
# auth_key = os.environ['auth_key']
    
TOKEN = 'NTI0NjUxODUzODg0MDMxMDA1.DvrNow.keCGf4G1SOPc4fEf6U6QUsJwoKw'

client = discord.Client()
dev_id = "2557"
auth_key = "E9A6FA1D226C45B1AAF8321822937182"

paladins = PaladinsClient(dev_id, auth_key)

def format_data(df, width=4):
    
    str_list = []

    for i in range(df.shape[0]):
        cur_row = []
        for j in range(df.shape[1]):
            if j==0:
                print(i,j)
                cur_row.append(str(df.iloc[i][j]).ljust(15))
            elif j==1:
                cur_row.append(str(df.iloc[i][j]).ljust(10))
            else:
                cur_row.append(str(df.iloc[i][j]).center(width))
        cur_row = " | ".join(cur_row)
        str_list.append(cur_row)
        
    str_list = "\n".join(str_list)
    
    return str_list

def format_data2(df, width=15):
    
    df.insert(0, "Property", ["Player", "Champion", "Damage", "Taken", "Shielding", "Healing", "KDA", "Party"])
    df.insert(6, "Property", ["Player", "Champion", "Damage", "Taken", "Shielding", "Healing", "KDA", "Party"], 
          allow_duplicates=True)

    str_list1 = []
    str_list2 = []
    
    # Loop through all rows except top row which contains player names
    for i in range(1, df.shape[0]):
        
        # Loop through columns 0 - 5 [field names + 5 players]
        cur_row1 = []
        for j in range(0, 6):
            if j==0:
                cur_row1.append(str(df.iloc[i, j]).ljust(10))
            else:
                cur_row1.append(str(df.iloc[i, j]).center(width))
        cur_row1 = " | ".join(cur_row1)
        str_list1.append(cur_row1)
        
        # Loop through columns 6 - 11 [field names + 5 players]
        cur_row2 = []
        for j in range(6, 12):
            if j==6:
                cur_row2.append(str(df.iloc[i, j]).ljust(10))
            else:
                cur_row2.append(str(df.iloc[i, j]).center(width))
        cur_row2 = " | ".join(cur_row2)
        str_list2.append(cur_row2)
        
    str_list1 = "\n".join(str_list1)
    str_list2 = "\n".join(str_list2)
    
    
    # Prepare headers with player names
    cols_list = list(df.iloc[0,:])
    col_str1 = " | ".join([ele.center(15) for ele in cols_list[1:6]])
    col_str1 = " | ".join([cols_list[0].ljust(10), col_str1])
    col_str2 = " | ".join([ele.center(15) for ele in cols_list[7:]])
    col_str2 = " | ".join([cols_list[6].ljust(10), col_str2])

    return col_str1, str_list1, col_str2, str_list2


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!current'):
        msg = message.content.split(" ")
        player_name = msg[1]
        
        print("\n\n\n--------------------------------------------\n")
        player_status = paladins.getPlayerStatus(player_name)
        if player_status['status'][0] != 3:
            await client.send_message(message.channel, "Could not get live match information for {}".format(player_name))
        else:
            live_match_id = player_status['Match'][0]
            data = paladins.getMatchPlayerDetails(live_match_id)
            
            player_info = data.sort_values('taskForce')[['ChampionName', 'playerName']]
            team1_info = player_info[:5]
            team2_info = player_info[5:]
            queue_id = data['Queue'][0]
            
            d1 = paladins.getAllData(team1_info, queue_id)

            width=4
            cols_list = list(d1.columns)
            col_str = " | ".join([ele.center(width) for ele in cols_list[2:]])
			
            col_str = " | ".join([cols_list[0].ljust(15), cols_list[1].ljust(10), col_str])
			
            await client.send_message(message.channel, "```" + col_str + "```")
			# await client.send_message(message.channel, "\n{}".format("-"*80))
            await client.send_message(message.channel, "```python\n" + format_data(d1) + "\n```")
			# await client.send_message(message.channel, "\n{}".format("-"*80))
            d2 = paladins.getAllData(team2_info, queue_id)
            await client.send_message(message.channel, "```python\n" + format_data(d2) + "\n```")
	
    elif message.content.startswith('!wins'):
        msg = message.content.split(" ")
        player_name = msg[1]
        if len(msg)==2:
            matches_count = 50
        else:
            matches_count = min(50, int(msg[2]))
        wins, matches_count = paladins.getWinRate(player_id=player_name, last_matches_count=matches_count)
        rate = str(round(wins/matches_count*100, 2))
		
        await client.send_message(message.channel, "```python\n Player {} won {} of the last {} matches with a win rate of {}%```".format(
		player_name, wins, matches_count, rate))

    elif message.content.startswith('!last'):
        msg = message.content.split(" ")
        player_name = msg[1]
        
        data = paladins.getLastMatchData(player_id=player_name)
        team1_names, team1_data, team2_names, team2_data = format_data2(data, width=8)
        
        # await client.send_message(message.channel, "```" + team1_names + "```")
        await client.send_message(message.channel, "```\n" + team1_data + "\n```")
        
        # await client.send_message(message.channel, "```" + team2_names + "```")
        await client.send_message(message.channel, "```\n" + team2_data + "\n```")
        
		
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)
