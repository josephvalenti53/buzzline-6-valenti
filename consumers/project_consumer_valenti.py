import os
import json
from collections import defaultdict
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# Import functions from local modules
from utils.utils_consumer import create_kafka_consumer
from utils.utils_logger import logger

# Load Environment Variables
load_dotenv()

def get_kafka_topic() -> str:
    topic = os.getenv("BUZZ_TOPIC", "unknown_topic")
    logger.info(f"Kafka topic: {topic}")
    return topic

def get_kafka_consumer_group_id() -> str:
    group_id: str = os.getenv("BUZZ_CONSUMER_GROUP_ID", "default_group")
    logger.info(f"Kafka consumer group id: {group_id}")
    return group_id

# Set up data structures
season_counts = defaultdict(lambda: defaultdict(int))  # Nested dictionary to store counts per season

# Set up live visuals
fig, ax = plt.subplots()
plt.ion()

# Define a color mapping for authors
author_colors = {
    "Homer": "yellow",
    "Bart": "red",
    "Marge": "blue",
    "Lisa": "black",
    "Maggie": "pink",
}

def update_chart():
    """Update the live chart with the latest counts, including percentage labels."""
    ax.clear()
    sorted_seasons = sorted(season_counts.keys(), key=int)
    bottom_counts = [0] * len(sorted_seasons)
    bars = []
    total_messages_per_season = {season: sum(season_counts[season].values()) for season in sorted_seasons}
    
    for author, color in author_colors.items():
        author_message_counts = [season_counts[season].get(author, 0) for season in sorted_seasons]
        bars.append(ax.bar(sorted_seasons, author_message_counts, bottom=bottom_counts, color=color, label=author))
        
        for i, count in enumerate(author_message_counts):
            if count > 0:
                percentage = (count / total_messages_per_season[sorted_seasons[i]]) * 100
                text_color = "black" if author in ["Homer", "Maggie"] else "white"
                ax.text(sorted_seasons[i], bottom_counts[i] + count / 2, f"{percentage:.1f}%", ha='center', va='center', fontsize=8, color=text_color)
        
        bottom_counts = [bottom + count for bottom, count in zip(bottom_counts, author_message_counts)]
    
    ax.set_xlabel("Seasons")
    ax.set_ylabel("Message Counts")
    ax.set_title("The Simpsons Most Memorable Leader (Seasons 1-30)")
    ax.set_xticks(sorted_seasons)
    ax.set_xticklabels(sorted_seasons, rotation=45, ha="right")
    ax.legend()
    plt.tight_layout()
    plt.draw()
    plt.pause(0.01)

def process_message(message: str) -> None:
    try:
        logger.debug(f"Raw message: {message}")
        message_dict: dict = json.loads(message)
        logger.info(f"Processed JSON message: {message_dict}")

        if isinstance(message_dict, dict):
            author = message_dict.get("author", "unknown")
            season = message_dict.get("season", "unknown")
            logger.info(f"Message received from author: {author} in season: {season}")

            season_counts[season][author] += 1
            logger.info(f"Updated season counts: {dict(season_counts)}")

            update_chart()
            logger.info(f"Chart updated successfully for message: {message}")
        else:
            logger.error(f"Expected a dictionary but got: {type(message_dict)}")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON message: {message}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def main() -> None:
    logger.info("START consumer.")
    topic = get_kafka_topic()
    group_id = get_kafka_consumer_group_id()
    logger.info(f"Consumer: Topic '{topic}' and group '{group_id}'...")

    consumer = create_kafka_consumer(topic, group_id)
    logger.info(f"Polling messages from topic '{topic}'...")

    try:
        for message in consumer:
            message_str = message.value
            logger.debug(f"Received message at offset {message.offset}: {message_str}")
            process_message(message_str)
    except KeyboardInterrupt:
        logger.warning("Consumer interrupted by user.")
    except Exception as e:
        logger.error(f"Error while consuming messages: {e}")
    finally:
        consumer.close()
        logger.info(f"Kafka consumer for topic '{topic}' closed.")

    logger.info(f"END consumer for topic '{topic}' and group '{group_id}'.")

if __name__ == "__main__":
    main()
    plt.ioff()
    plt.show()
