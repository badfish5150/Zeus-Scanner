import os
import json
import time
import urllib2

from base64 import b64decode

import lib.core.settings


def __get_encoded_string(path="{}/etc/auths/whois_auth"):
    with open(path.format(os.getcwd())) as log:
        return log.read()


def __get_n(encoded):
    return encoded.split(":")[-1]


def __decode(encoded, n):
    token = encoded.split(":")[0]
    for _ in range(0, n):
        token = b64decode(token)
    return token


def __get_token():
    encoded = __get_encoded_string()
    n = __get_n(encoded)
    token = __decode(encoded, int(n))
    return token


def gather_raw_whois_info(domain):
    """
    get the raw JSON data for from the whois API
    """
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": "Token {}".format(__get_token()),
    }
    request = urllib2.Request(
        lib.core.settings.WHOIS_JSON_LINK.format(domain), headers=auth_headers
    )
    data = urllib2.urlopen(request).read()
    _json_data = json.loads(data)
    return _json_data


def _pretty_print_json(data, sort=True, indentation=4):
    return json.dumps(data, sort_keys=sort, indent=indentation)


def get_interesting(raw_json):
    """
    return the interesting aspects of the whois lookup from the raw JSON data
    """
    nameservers = raw_json["nameservers"]
    user_contact = raw_json["contacts"]
    reg_info = raw_json["registrar"]
    return nameservers, user_contact, reg_info


def human_readable_display(domain, interesting):
    """
    create a human readable display from the given whois lookup
    """
    data_sep = "-" * 30
    servers, contact, reg = interesting
    total_servers, total_contact, total_reg = len(servers), len(contact), len(reg)
    print(data_sep)
    print("[!] Domain {}".format(domain))
    if total_servers > 0:
        print("[!] Found a total of {} servers".format(total_servers))
        print(_pretty_print_json(servers))
    else:
        print("[x] No server information found")
    if total_contact > 0:
        print("[!] Found contact information")
        print(_pretty_print_json(contact))
    else:
        print("[x] No contact information found")
    if total_reg > 0:
        print("[!] Found register information")
        print(_pretty_print_json(reg))
    else:
        print("[x] No register information found")
    print(data_sep)


def whois_lookup_main(domain, **kwargs):
    """
    main function
    """
    # sleep a little bit so that WhoIs doesn't stop us from making requests
    verbose = kwargs.get("verbose", False)
    timeout = kwargs.get("timeout", None)
    domain = lib.core.settings.replace_http(domain)
    lib.core.settings.logger.info(lib.core.settings.set_color(
        "performing WhoIs lookup on given domain '{}'...".format(domain)
    ))
    if timeout is not None:
        time.sleep(timeout)
    raw_information = gather_raw_whois_info(domain)
    lib.core.settings.logger.info(lib.core.settings.set_color(
        "discovered raw information...", level=25
    ))
    lib.core.settings.logger.info(lib.core.settings.set_color(
        "gathering interesting information..."
    ))
    interesting_data = get_interesting(raw_information)
    if verbose:
        try:
            human_readable_display(domain, interesting_data)
        except (ValueError, Exception):
            lib.core.settings.logger.fatal(lib.core.settings.set_color(
                "unable to display any information from WhoIs lookup on domain '{}'...".format(domain), level=50
            ))
    lib.core.settings.write_to_log_file(
        raw_information, lib.core.settings.WHOIS_RESULTS_LOG_PATH,
        "{}-whois.json".format(domain)
    )