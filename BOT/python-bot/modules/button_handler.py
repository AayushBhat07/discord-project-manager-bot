class ButtonHandler:
    def __init__(self):
        self.handlers = {
            'btn_help': self.handle_help,
            'btn_ai': self.handle_ai,
            'btn_schedule': self.handle_schedule,
            'btn_github': self.handle_github,
        }

    def handle(self, custom_id, interaction):
        handler = self.handlers.get(custom_id)
        if handler:
            return handler(interaction)
        return None

    def handle_help(self, interaction):
        from modules.banner_ui import BannerUI
        banner = BannerUI()
        return {
            'embed': banner.create_features_list_embed(),
            'ephemeral': True,
            'show_banner': False
        }

    def handle_ai(self, interaction):
        from modules.ai_handler import AIHandler
        ai = AIHandler()
        return {
            'embed': ai.create_ai_banner(),
            'ephemeral': True,
            'show_banner': False
        }

    def handle_schedule(self, interaction):
        from modules.banner_ui import BannerUI
        banner = BannerUI()
        return {
            'embed': banner.create_info_embed(
                '⏰ Scheduling',
                'Use `!schedule <cron> "<message>"` to schedule commits.\n'
                'Example: `!schedule "0 9 * * *" "Daily commit"`'
            ),
            'ephemeral': True,
            'show_banner': False
        }

    def handle_github(self, interaction):
        from modules.banner_ui import BannerUI
        banner = BannerUI()
        return {
            'embed': banner.create_info_embed(
                '📡 GitHub Setup',
                'Use `!setup github <pat> <repo-url> [branch]` to configure.\n'
                'Example: `!setup github ghp_xxx https://github.com/user/repo main`'
            ),
            'ephemeral': True,
            'show_banner': False
        }
