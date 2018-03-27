from .manifest import TASKS, REPORTS, STATISTICS
from nudgebot.bot import Bot


def main():
    bot = Bot(TASKS, REPORTS, STATISTICS)
    bot.run()


if __name__ == '__main__':
    main()
