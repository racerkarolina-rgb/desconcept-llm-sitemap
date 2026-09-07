#!/usr/bin/env python3
"""SFTP upload adapter for the DES Concept OpenAI Ads feed."""

import os
import subprocess

import openai_feed_sync as feed


def upload_with_openssh(local_file):
    host = os.environ["OPENAI_SFTP_HOST"]
    port = os.environ.get("OPENAI_SFTP_PORT", "443")
    username = os.environ["OPENAI_SFTP_USERNAME"]
    env = os.environ.copy()
    env["SSHPASS"] = os.environ["OPENAI_SFTP_PASSWORD"]
    batch = f'put "{local_file}" "/{feed.REMOTE_FILENAME}"\nbye\n'
    subprocess.run(
        [
            "sshpass", "-e", "sftp", "-P", port,
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "PreferredAuthentications=password,keyboard-interactive",
            f"{username}@{host}",
        ],
        input=batch,
        text=True,
        env=env,
        check=True,
    )


feed.upload = upload_with_openssh
feed.main()
