from module.base.decorator import Config
from module.campaign.campaign_ui import CampaignUI
from module.exception import CampaignEnd, ScriptError, MapEnemyMoved
from module.logger import logger
from module.map.map import Map
from module.map.map_base import CampaignMap


class CampaignBase(Map, CampaignUI):
    FUNCTION_NAME_BASE = 'battle_'
    MAP: CampaignMap

    def battle_default(self):
        if self.clear_enemy():
            return True

        logger.warning('No battle executed.')
        return False

    def battle_boss(self):
        if self.brute_clear_boss():
            return True

        logger.warning('No battle executed.')
        return False

    @Config.when(POOR_MAP_DATA=True, MAP_CLEAR_ALL_THIS_TIME=False)
    def battle_function(self):
        logger.info('Using function: battle_with_poor_map_data')
        if self.fleet_2_break_siren_caught():
            return True
        self.clear_all_mystery()

        if self.battle_count >= 3:
            self.pick_up_ammo()

        if self.map.select(is_boss=True):
            if self.brute_clear_boss():
                return True
        else:
            if self.clear_siren():
                return True
            return self.clear_enemy()

        return False

    @Config.when(MAP_CLEAR_ALL_THIS_TIME=True)
    def battle_function(self):
        logger.info('Using function: clear_all')
        if self.fleet_2_break_siren_caught():
            return True
        self.clear_all_mystery()

        if self.battle_count >= 3:
            self.pick_up_ammo()

        remain = self.map.select(is_enemy=True, is_boss=False)
        logger.info(f'Enemy remain: {remain}')
        if remain.count > 0:
            if self.clear_siren():
                return True

            self.clear_mechanism()

            return self.battle_default()
        else:
            backup = self.config.FLEET_BOSS
            if self.config.FLEET_2 != 0:
                self.config.FLEET_BOSS = 2
            result = self.battle_boss()
            self.config.FLEET_BOSS = backup
            return result

    @Config.when(MAP_CLEAR_ALL_THIS_TIME=False, POOR_MAP_DATA=False)
    def battle_function(self):
        func = self.FUNCTION_NAME_BASE + 'default'
        for extra_battle in range(10):
            if hasattr(self, self.FUNCTION_NAME_BASE + str(self.battle_count - extra_battle)):
                func = self.FUNCTION_NAME_BASE + str(self.battle_count - extra_battle)
                break

        logger.info(f'Using function: {func}')
        func = self.__getattribute__(func)

        result = func()

        return result

    def execute_a_battle(self):
        logger.hr(f'{self.FUNCTION_NAME_BASE}{self.battle_count}', level=2)
        prev = self.battle_count
        result = False
        for _ in range(10):
            try:
                result = self.battle_function()
                break
            except MapEnemyMoved:
                if self.battle_count > prev:
                    result = True
                    break
                else:
                    continue

        if not result:
            logger.warning('ScriptError, No combat executed.')
            if self.config.ENABLE_EXCEPTION:
                raise ScriptError('No combat executed.')
            else:
                logger.warning('ScriptError, Withdrawing because enable_exception = no')
                self.withdraw()

        return result

    def run(self):
        logger.hr(self.ENTRANCE, level=2)
        self.handle_spare_fleet()
        self.emotion.wait()
        self.ENTRANCE.area = self.ENTRANCE.button
        self.enter_map(self.ENTRANCE, mode=self.config.CAMPAIGN_MODE)
        self.handle_map_fleet_lock()
        self.map_init(self.MAP)

        for _ in range(20):
            try:
                self.execute_a_battle()
            except CampaignEnd:
                logger.hr('Campaign end')
                return True

        logger.warning('Battle function exhausted.')
        if self.config.ENABLE_EXCEPTION:
            raise ScriptError('Battle function exhausted.')
        else:
            logger.warning('ScriptError, Battle function exhausted, Withdrawing because enable_exception = no')
            self.withdraw()
