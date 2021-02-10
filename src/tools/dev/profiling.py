import cProfile
import pstats

from tests.integration.features_integration_test import (
    test_advertisement,
    test_anti_adblock,
    test_cookies,
    test_cookies_in_html,
    test_easy_privacy,
    test_easylist_adult,
    test_easylist_germany,
    test_extract_from_files,
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
]

profile = cProfile.Profile()
for func in test_functions:
    try:
        profile.runcall(func)
    except KeyError:
        pass
ps = pstats.Stats(profile)
ps.sort_stats("cumtime")
ps.print_stats("features")
