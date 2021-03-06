from module.base.button import Button
from module.base.utils import area_offset, get_color
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.exception import CampaignNameError
from module.ui.assets import WAR_ARCHIVES_CHECK
from module.ui.page import page_archives
from module.ui.switch import Switch
from module.war_archives.assets import WAR_ARCHIVES_EX_ON, WAR_ARCHIVES_SP_ON, WAR_ARCHIVES_CAMPAIGN_CHECK
from module.war_archives.dictionary import dic_archives_template

WAR_ARCHIVES_SWITCH = Switch('War_Archives_switch', is_selector=True)
WAR_ARCHIVES_SWITCH.add_status('ex', WAR_ARCHIVES_EX_ON)
WAR_ARCHIVES_SWITCH.add_status('sp', WAR_ARCHIVES_SP_ON)


class CampaignBase(CampaignBase_):
    # Helper variable to keep track of whether is the first runthrough
    first_run = True

    def _get_archives_entrance(self, name):
        """
        Create entrance button to target archive campaign
        using a template acquired by event folder name

        TODO: Each server have different selectable campaign
              Need something similar to commission to scroll
              or turn page. CN/JP have more than 4 atm.

        Args:
            name(str): event folder name
        """
        template = dic_archives_template[name]

        sim, point = template.match_result(self.device.image)
        if sim < 0.85:
            raise CampaignNameError

        button = area_offset(area=(-12, -12, 44, 32), offset=point)
        color = get_color(self.device.image, button)
        entrance = Button(area=button, color=color, button=button, name=name)
        return entrance

    def ui_goto_archives_campaign(self, mode='ex'):
        """
        Performs the operations needed to transition
        to target archive's campaign stage map
        """
        # On first run regardless of current location
        # even in target stage map, start from page_archives
        # For subsequent runs when neither reward or
        # stop_triggers occur, no need perform operations
        result = True
        if self.first_run or not self.appear(WAR_ARCHIVES_CAMPAIGN_CHECK, offset=(20, 20)):
            result = self.ui_ensure(destination=page_archives)

            WAR_ARCHIVES_SWITCH.set(mode, main=self)
            self.handle_stage_icon_spawn()

            archives_entrance = self._get_archives_entrance(self.config.WAR_ARCHIVES_NAME)
            self.ui_click(archives_entrance, appear_button=WAR_ARCHIVES_CHECK, check_button=WAR_ARCHIVES_CAMPAIGN_CHECK,
                          skip_first_screenshot=True)
        self.handle_stage_icon_spawn()

        # Subsequent runs all set False
        if self.first_run:
            self.first_run = False

        return result

    def ui_goto_event(self):
        """
        Overridden to handle specifically transitions
        to target ex event in page_archives
        """
        return self.ui_goto_archives_campaign(mode='ex')

    def ui_goto_sp(self):
        """
        Overridden to handle specifically transitions
        to target sp event in page_archives
        """
        return self.ui_goto_archives_campaign(mode='sp')
