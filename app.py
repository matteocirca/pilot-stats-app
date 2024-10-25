import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(layout="wide")

st.title("Mechanic Conversations Dashboard")

# upload user_stats.json
user_stats_file = st.file_uploader("Upload user_stats.json", type="json")
if user_stats_file:
    user_stats = json.load(user_stats_file)
    user_stats_df = pd.DataFrame(user_stats)

# upload user_conversations.json
user_conversations_file = st.file_uploader("Upload user_conversations.json", type="json")
if user_conversations_file:
    user_conversations = json.load(user_conversations_file)
    user_conversations_df = pd.DataFrame(user_conversations)

# proceed if both files are uploaded
if user_stats_file and user_conversations_file:
    # convert date strings to datetime objects
    user_stats_df['last_login'] = pd.to_datetime(user_stats_df['last_login'])
    user_conversations_df['created_at'] = pd.to_datetime(user_conversations_df['created_at'])
    user_conversations_df['updated_at'] = pd.to_datetime(user_conversations_df['updated_at'])

    # divide the page into two columns
    col1, col2 = st.columns(2)

    # left column: global stats
    with col1:
        st.header("Global Stats")

        # total number of mechanics
        total_mechanics = user_stats_df['email'].nunique()
        st.metric("Total Mechanics", total_mechanics)

        # total number of chats
        total_chats = len(user_conversations_df)
        st.metric("Total Chats", total_chats)

        # number of verified answers (open_search=False)
        verified_answers = len(user_conversations_df[user_conversations_df['open_search'] == False])
        st.metric("Verified Answers", f"{verified_answers}/{total_chats}")

        # engagement: number of chats with messages length > 4
        engaged_chats = user_conversations_df[user_conversations_df['messages'].apply(lambda x: len(x) > 4)]
        num_engaged_chats = len(engaged_chats)
        st.metric("Engaged Chats (messages > 4)", num_engaged_chats)

        # average number of messages per chat
        user_conversations_df['num_messages'] = user_conversations_df['messages'].apply(len)
        avg_messages_per_chat = user_conversations_df['num_messages'].mean()
        st.metric("Average Messages per Chat", f"{avg_messages_per_chat:.2f}")

        # active mechanics (mechanics who have at least one chat)
        active_mechanics = user_conversations_df['email'].nunique()
        st.metric("Active Mechanics", active_mechanics)

        # average number of chats per mechanic
        avg_chats_per_mechanic = user_conversations_df.groupby('email').size().mean()
        st.metric("Average Chats per Mechanic", f"{avg_chats_per_mechanic:.2f}")

        # most common error codes
        st.header("Most Common Error Codes")
        all_dtcs = [dtc for dtcs in user_conversations_df['dtcs'] for dtc in dtcs]
        dtc_counts = pd.Series(all_dtcs).value_counts()
        st.write(dtc_counts)

        # most common internal error codes
        st.header("Most Common Internal Error Codes")
        internal_dtcs = [internal_error_code for dtcs in user_conversations_df['internal_error_codes'] for internal_error_code in dtcs]
        internal_dtc_counts = pd.Series(internal_dtcs).value_counts()
        st.write(internal_dtc_counts)

        # most common manufacturers
        st.header("Most Common Manufacturers")
        manufacturer_counts = user_conversations_df['manufacturer'].value_counts()
        st.write(manufacturer_counts)

        # most common car models
        st.header("Most Common Car Models")
        model_manufacturer_counts = user_conversations_df.groupby(['manufacturer', 'model']).size().reset_index(name='count')
        model_manufacturer_counts = model_manufacturer_counts.sort_values(by='count', ascending=False)
        model_manufacturer_counts = model_manufacturer_counts.reset_index(drop=True)
        model_manufacturer_counts.index = model_manufacturer_counts.index + 1
        st.write(model_manufacturer_counts)

        # most active mechanics
        st.header("Most Active Mechanics")
        mechanic_chat_counts = user_conversations_df.groupby('email').size().sort_values(ascending=False)
        mechanic_chat_counts = mechanic_chat_counts.reset_index(name='number of chats')
        mechanic_chat_counts.index = mechanic_chat_counts.index + 1
        st.write(mechanic_chat_counts)

    # right column: mechanic stats and chats
    with col2:
        st.header("Select a Mechanic")
        mechanics = user_stats_df['email'].unique()
        selected_mechanic = st.selectbox("Choose a mechanic", mechanics)

        if selected_mechanic:
            mechanic_stats = user_stats_df[user_stats_df['email'] == selected_mechanic].iloc[0]
            mechanic_conversations = user_conversations_df[user_conversations_df['email'] == selected_mechanic]

            st.subheader(f"Stats for {selected_mechanic}")

            # display mechanic stats
            st.write(f"**Last Login:** {mechanic_stats['last_login']}")
            st.write(f"**Login Count:** {int(mechanic_stats['login_count'])}")
            st.write(f"**Login History:**")
            st.write(mechanic_stats['login_history'])

            # select a chat
            st.subheader("Select a Chat")
            mechanic_conversations = mechanic_conversations.sort_values(by='updated_at', ascending=False)
            chat_titles = mechanic_conversations['title'].tolist()

            if chat_titles:
                selected_chat_title = st.selectbox("Select a chat", chat_titles)
                if selected_chat_title:
                    selected_chat = mechanic_conversations[mechanic_conversations['title'] == selected_chat_title].iloc[0]

                    # display chat details
                    st.subheader(f"Chat: {selected_chat_title}")
                    st.write(f"**Vehicle:** {selected_chat['manufacturer']} {selected_chat['model']} {int(selected_chat['year'])}")
                    st.write(f"**Mileage:** {selected_chat['mileage']}")
                    st.write(f"**Error Codes:** {', '.join(selected_chat['dtcs'])}")

                    # display messages excluding system messages
                    st.write("**Messages:**")
                    messages = selected_chat['messages']
                    for message in messages:
                        if message['role'] != 'system':
                            if message['role'] == 'user':
                                st.markdown(f"**User:** {message['content']}")
                            else:
                                st.markdown(f"**Assistant:** {message['content']}")
            else:
                st.write("No chats available for this mechanic.")
