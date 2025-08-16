"""
Output handler for printing and saving headlines.
"""
import logging
import os


class OutputHandler:
    """
    Handles output of headlines to console and files.
    """

    @staticmethod
    def print_headlines(headlines: list[str]) -> None:
        """
        Print headlines to the console in a formatted way.
        """
        print("\n--- News Headlines ---")
        for idx, headline in enumerate(headlines, 1):
            print(f"{idx}. {headline}")
        print(f"\nTotal headlines: {len(headlines)}\n")

    @staticmethod
    def save_headlines(headlines: list[str], filepath: str) -> None:
        """
        Save headlines to a plain text file, one per line.
        """
        logger = logging.getLogger("simple_news_scraper.output")
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                for headline in headlines:
                    f.write(headline + "\n")
        except Exception as exc:
            logger.error(f"Failed to write to file {filepath}: {exc}")
            raise
