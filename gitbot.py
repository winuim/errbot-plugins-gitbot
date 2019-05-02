from errbot import BotPlugin, botcmd, arg_botcmd
from itertools import chain
import git
import os
import argparse
import re
import subprocess


class GitBot(BotPlugin):
    """Git plugin for Errbot"""
    CONFIG_TEMPLATE = {
        'GIT_WORKDIR': '/app/srv/git_work/',
    }
    _git_dirname = None

    def configure(self, configuration):
        if configuration is not None and configuration != {}:
            config = dict(
                chain(self.CONFIG_TEMPLATE.items(), configuration.items()))
        else:
            config = self.CONFIG_TEMPLATE
        super(GitBot, self).configure(config)

    def get_configuration_template(self):
        return self.CONFIG_TEMPLATE

    def check_configuration(self, configuration):
        pass

    @arg_botcmd('dirname', type=str)
    def git_setDir(self, msg, dirname):
        """git setDir dirname"""
        repo_path = os.path.join(self.CONFIG_TEMPLATE['GIT_WORKDIR'], dirname)

        if os.path.exists(repo_path):
            self._git_dirname = dirname
            return f"{dirname} exists."
        else:
            return f"{dirname} don't exists."

    @botcmd
    def git_getDir(self, msg, args):
        """git getDir"""
        return self._git_dirname

    @arg_botcmd('--all', dest='opt_all', action='store_true')
    def git_branch(self, msg, opt_all):
        """git branch"""
        repo_path, _err = self.get_repo_path(self._git_dirname)
        if _err:
            return _err

        repo = git.Repo(repo_path)
        ret = []
        for item in repo.branches:
            if repo.active_branch == item:
                ret.append(f"* {item}\n")
            else:
                ret.append(f"  {item}\n")
        if opt_all:
            for item in repo.remotes.origin.refs:
                remote_path = re.sub('^refs/', '', item.path)
                ret.append(f"  {remote_path} -> {item.name}\n")

        return '\n'.join(ret)

    @arg_botcmd('url', type=str)
    def git_clone(self, msg, url):
        """git clone url"""
        if self._git_dirname is None:
            return "needs to git_setDir."
        repo_path = os.path.join(self.CONFIG_TEMPLATE['GIT_WORKDIR'],
                                 self._git_dirname)
        if os.path.exists(repo_path):
            return f"{self._git_dirname} don't exists."

        repo = git.Repo.clone_from(
            url,
            os.path.join(self.CONFIG_TEMPLATE['GIT_WORKDIR'],
                         self._git_dirname))
        return repo

    @arg_botcmd('user_email', type=str)
    @arg_botcmd('user_name', type=str)
    def git_config(self, msg, user_name, user_email):
        """git config"""
        repo_path, _err = self.get_repo_path(self._git_dirname)
        if _err:
            return _err

        repo = git.Repo(repo_path)
        repo.config_writer().set_value('user', 'name', user_name).release()
        repo.config_writer().set_value('user', 'email', user_email).release()

    @botcmd(admin_only=True)
    def cmd(self, msg, args):
        """whoami"""
        try:
            command = 'whoami'
            if args:
                re_quotation = re.compile(r'("[^"]+")|(\'[^\']+\')|([^ ]+)')
                command = list(
                    filter(lambda x: x != "",
                           chain.from_iterable(re_quotation.findall(args))))
            cmd_call = subprocess.Popen(
                command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        except Exception as _err:
            return _err
        tags, _err = cmd_call.communicate()
        return_code = cmd_call.returncode
        return f"return_code={return_code}\n{command}\n{tags.decode('utf-8')}\n"

    def get_repo_path(self, dir_name):
        if dir_name is None:
            return None, "needs to dir_name"
        repo_path = os.path.join(self.CONFIG_TEMPLATE['GIT_WORKDIR'], dir_name)
        if not os.path.exists(repo_path):
            return None, f"{dir_name} don't exists."

        return repo_path, None