import cProfile
import pstats

from pyinstrument import Profiler

from tests.integration.features_integration_test import (
    test_advertisement,
    test_anti_adblock,
    test_cookies,
    test_cookies_in_html,
    test_easy_privacy,
    test_easylist_adult,
    test_easylist_germany,
    test_extract_from_files,
    test_fanboy_annoyance,
    test_fanboy_notification,
    test_fanboy_social_media,
    test_g_d_p_r,
    test_iframe_embeddable,
    test_javascript,
    test_log_in_out,
    test_malicious_extensions,
    test_metatag_explorer,
    test_paywalls,
    test_pop_up,
    test_reg_wall,
)
from tests.integration.security_test import test_start
from tests.unit.accessibility_test import test_accessibility

test_functions = [
    test_advertisement,
    test_paywalls,
    test_easylist_adult,
    test_cookies_in_html,
    test_easy_privacy,
    test_malicious_extensions,
    test_extract_from_files,
    test_fanboy_social_media,
    test_pop_up,
    test_log_in_out,
    test_g_d_p_r,
    test_easylist_germany,
    test_anti_adblock,
    test_fanboy_notification,
    test_reg_wall,
    test_iframe_embeddable,
    test_javascript,
    test_cookies,
    test_metatag_explorer,
    test_accessibility,
    test_start,
    test_fanboy_annoyance,
]


def call_test_funcs():
    for func in test_functions:
        try:
            func()
        except (KeyError, TypeError):
            pass


# cProfile
profile = cProfile.Profile()
profile.runcall(call_test_funcs)
ps = pstats.Stats(profile)
ps.sort_stats("cumtime")
ps.print_stats("features")

# pyinstrument
profiler = Profiler()
profiler.start()

call_test_funcs()

profiler.stop()

print(profiler.output_text(unicode=True, color=True))
