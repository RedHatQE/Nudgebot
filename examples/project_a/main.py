from assets import celery_runner, bot


def main():
    """Running celery and then runs the bot's mainloop"""
    celery_runner.start()
    bot.mainloop()


if __name__ == '__main__':
    main()
