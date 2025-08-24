from flask import Flask, request
import xml.etree.ElementTree as ET
import requests
import json

app = Flask(__name__)

@app.route('/youtube-webhook', methods=['GET', 'POST'])
def youtube_webhook():
    if request.method == 'GET':
        # Handle subscription verification
        challenge = request.args.get('hub.challenge')
        mode = request.args.get('hub.mode')
        
        if challenge and mode == 'subscribe':
            print(f"Verified YouTube subscription")
            return challenge, 200
        return 'Not found', 404
    
    elif request.method == 'POST':
        # Parse YouTube RSS notification
        xml_data = request.get_data().decode('utf-8')
        root = ET.fromstring(xml_data)
        
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015'
        }
        
        for entry in root.findall('atom:entry', ns):
            video_id = entry.find('yt:videoId', ns).text
            channel_id = entry.find('yt:channelId', ns).text
            title = entry.find('atom:title', ns).text
            published = entry.find('atom:published', ns).text
            
            # Trigger download workflow
            trigger_video_download({
                'video_id': video_id,
                'channel_id': channel_id,
                'title': title,
                'published': published,
                'url': f'https://www.youtube.com/watch?v={video_id}'
            })
        
        return 'OK', 200

def trigger_video_download(video_data):
    """This function will trigger the CrewAI workflow to download the video."""
    # In a real application, you would have a more robust way to trigger the workflow.
    # For now, we will just print the video data.
    print(f"Triggering download for video: {json.dumps(video_data, indent=2)}")

def subscribe_to_channel(channel_id, webhook_url):
    """Subscribe to YouTube channel using PubSubHubbub"""
    data = {
        'hub.mode': 'subscribe',
        'hub.topic': f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}',
        'hub.callback': webhook_url,
        'hub.verify': 'sync',
        'hub.lease_seconds': '432000'  # 5 days
    }
    
    response = requests.post(
        'https://pubsubhubbub.appspot.com/subscribe',
        data=data
    )
    
    return response.status_code == 204

if __name__ == '__main__':
    # In a production environment, you would use a proper WSGI server like Gunicorn or uWSGI.
    # For development, we can run the Flask app directly.
    # You will also need to expose this webhook to the internet using a tool like ngrok
    # for PubSubHubbub to be able to reach it.
    app.run(port=8080)
