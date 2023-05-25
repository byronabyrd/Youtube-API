import googleapiclient.discovery
import googleapiclient.errors
import requests
import time
import pandas as pd
import psycopg2 as ps
from psycopg2 import Error
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Date, BigInteger, update, UniqueConstraint, insert, exc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import exists
from sqlalchemy.ext.declarative import declarative_base
import os
import sys
from getpass import getpass

# Keys
API_KEY = os.getenv('API_KEY')

if not API_KEY:
    API_KEY = getpass('Please enter your API Key: ')

# Initializes YouTube API client
youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=API_KEY)

# Prompts user for list of usernames
def get_usernames():
    usernames = input("Please enter a list of channel names, separated by commas: ")
    if not usernames:
        print("You must enter at least one username.")
        sys.exit(1)

    usernames = [name.strip() for name in usernames.split(",")]
    return usernames

# Retrieves channel ID based on username provided 
def get_youtube_channel_id(username):
    response = youtube.search().list(
        part="snippet",
        type="channel",
        q=username
        ).execute()
    # Error checking
    if response['pageInfo']['totalResults'] > 0:
        return response['items'][0]['id']['channelId']
    else:
        print(f"No channel found with username: {username}")
        return None

# Defines function to get data for each channel
def get_channel_details(df):
    # List to store individual channel data
    channel_data = []

    # Iterate through the list of channel names
    for username in usernames:
        # Get channel id for the current username
        channelId = get_youtube_channel_id(username)

        # If a channel id was found, create a DataFrame for this channel
        if channelId is not None:
            channel_df = pd.DataFrame({'channelId': [channelId],
                                       'username': [username]})
            channel_data.append(channel_df)

    # Concatenate all individual channel DataFrames
    if channel_data:
        df = pd.concat(channel_data, ignore_index=True)
        
    return df

# Originate channel name list variable as type list by invoking get_channel_names functions
usernames = get_usernames()

# Build our dataframe
df = pd.DataFrame(columns=["channelId", "username"])

# Populate the dataframe with channel data
df = get_channel_details(df)

# Build channel_ids list from df
channel_ids = df['channelId'].tolist()

# Connection parameters
db_name = os.getenv('DB_NAME')
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')

if not all([db_name, username, password, host, port]):
    print("Database environment variables are not set.")
    sys.exit(1)

# Create an engine instance
alchemyEngine = create_engine(f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{db_name}', pool_recycle=3600)

# Connect to PostgreSQL server
dbConnection = None

try:
    dbConnection = alchemyEngine.connect()
    print("Successfully connected to the database!")
except exc.SQLAlchemyError as e:
    print(f"An error occurred while trying to connect: {e}")
    sys.exit(1)  # Exit if cannot connect to the database

# Create a Session object
session = Session(bind=dbConnection)

if dbConnection:
    # Create channels table if it doesn't exist
    metadata = MetaData()
    channels = Table(
        'channels', metadata, 
        Column('channelId', String, primary_key = True), 
        Column('username', String),
    )
    metadata.create_all(alchemyEngine)  # Creates the table

    # Insert data into the table from the DataFrame
    try:
        for index, row in df.iterrows():
            try:
                stmt = insert(channels).values(channelId=row['channelId'], username=row['username'])
                session.execute(stmt)
                session.commit()
            except IntegrityError:
                session.rollback()
                session.execute(channels.update().where(channels.c.channelId==row['channelId']).values(username=row['username']))
                session.commit()
    except exc.SQLAlchemyError as e:
        print(f"An error occurred while inserting data: {e}")
        session.rollback()  # Rollback the transaction in case of error

    # Close the database connection
    session.close()
    dbConnection.close()

from googleapiclient.errors import HttpError

def get_videos(youtube, df, channel_ids):
  
  for channel_id in channel_ids:
    print(f'Getting videos for channel ID: {channel_id}')

    # Start without a page token
    pageToken = None
    
    while True:
      try:
        print(f"Making request with page token: {pageToken}")
        request = youtube.search().list(
          part="snippet",
          channelId=channel_id,
          maxResults=49,
          order="date",
          pageToken=pageToken
        )
        response = request.execute()
        time.sleep(1)

        video_data = []  # List to store individual video data
      
        # for loop navigates response .json and save data to python variables below
        if 'items' in response:
            for video in response['items']:
              if video['id']['kind'] == "youtube#video":
                  video_id = video['id']['videoId']
                  channel_id = video['snippet']['channelId']
                  video_title = video['snippet']['title']
                  video_title = str(video_title).replace("&amp;","")
                  upload_date = video['snippet']['publishedAt']
                  upload_date = str(upload_date).split("T")[0]

                  view_count, like_count, comment_count = get_video_details(youtube, video_id)
                  
                  video_df = pd.DataFrame({
                                          'video_id': [video_id],
                                          'channel_id': [channel_id],
                                          'video_title': [video_title],
                                          'upload_date': [upload_date],
                                          'view_count': [view_count],
                                          'like_count': [like_count],
                                          'comment_count': [comment_count]
                                          })
                  
                  video_data.append(video_df)
                  
            if video_data:
              df = pd.concat([df, *video_data], ignore_index=True)
              
            # Check if there are more pages of results
            if 'nextPageToken' in response:
              pageToken = response['nextPageToken']
            else:
              break  # If there are no more pages of results, break the loop
          
        else:
          print("No 'items' in response. The response was: ", response)

      except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        break
  
  return df

def get_video_details(youtube, video_id):
  print(f'Getting video details for Video ID: {video_id}')
  try:
    request = youtube.videos().list(
      part="statistics",
      id=video_id
    )
    response = request.execute()

    view_count = response['items'][0]['statistics'].get('viewCount', 0)
    like_count = response['items'][0]['statistics'].get('likeCount', 0)
    comment_count = response['items'][0]['statistics'].get('commentCount', 0)

    return view_count, like_count, comment_count

  except HttpError as e:
    print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
    return 0, 0, 0

#main

# build our dataframe
df = pd.DataFrame(columns=["video_id","channel_id","video_title","upload_date","view_count","like_count","comment_count"])

df = get_videos(youtube, df, channel_ids)

# Create a new base for declarative models
Base = declarative_base()

# Connect to PostgreSQL server
dbConnection = None
try:
    dbConnection = alchemyEngine.connect()
    print("Successfully connected to the database!")
except exc.SQLAlchemyError as e:
    print(f"An error occurred while trying to connect: {e}")

# Create a Session object
session = Session(bind=dbConnection)

# Define the Videos table
class Videos(Base):
    __tablename__ = 'videos'
    
    video_id = Column(String, primary_key=True)
    channel_id = Column(String)
    video_title = Column(String)
    upload_date = Column(Date)
    view_count = Column(BigInteger)
    like_count = Column(BigInteger)
    comment_count = Column(BigInteger)

    __table_args__ = (UniqueConstraint('video_id', 'channel_id', name='unique_video_and_channel'), )

# Create the table
Base.metadata.create_all(alchemyEngine)

# Now, let's insert the data from the DataFrame into the videos table
for index, row in df.iterrows():
    # First, check if a row with this video_id and channel_id already exists
    exists_query = session.query(Videos).filter(Videos.video_id==row['video_id'], Videos.channel_id==row['channel_id']).first()

    if exists_query:
        # If the row exists, update it
        stmt = update(Videos).where(Videos.video_id==row['video_id'], Videos.channel_id==row['channel_id']).values(
            video_title=row['video_title'],
            upload_date=row['upload_date'],
            view_count=row['view_count'],
            like_count=row['like_count'],
            comment_count=row['comment_count']
        )
        session.execute(stmt)
    else:
        # If the row does not exist, insert it
        new_video = Videos(
            video_id=row['video_id'],
            channel_id=row['channel_id'],
            video_title=row['video_title'],
            upload_date=row['upload_date'],
            view_count=row['view_count'],
            like_count=row['like_count'],
            comment_count=row['comment_count']
        )
        session.add(new_video)

    try:
        session.commit()
    except exc.SQLAlchemyError as e:
        print(f"An error occurred while inserting data: {e}")
        session.rollback()  # Rollback the transaction in case of error

# Close the database connection
session.close()
dbConnection.close()
