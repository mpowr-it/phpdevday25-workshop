#!/usr/bin/env bash
# --
# @version: 1.0.0
# @purpose: Shell script to run when an interactive devbox shell is started.
# --

# export PYTHONWARNINGS="ignore::CryptographyDeprecationWarning"

#
# constants and variable scope
# --
C_DBX_INIT_PATH_ROOT="scripts/devbox/init"
C_DBX_INIT_ENTRYPOINT="dbx_init.sh"

#
# function: check baseline configuration and tool/package availability
# --
init_check() {

  # @info: this os identification process will be used later to provide additional init-scripts based on your os
  unameOut=$(uname -a)
  case "${unameOut}" in
    *Microsoft*)  C_DBX_OS="WSL"     ; C_DBX_INIT_PATH="${C_DBX_INIT_PATH_ROOT}/os_win64wsl" ;;
    *microsoft*)  C_DBX_OS="WSL2"    ; C_DBX_INIT_PATH="${C_DBX_INIT_PATH_ROOT}/os_win64wsl" ;;
    Linux*)       C_DBX_OS="Linux"   ; C_DBX_INIT_PATH="${C_DBX_INIT_PATH_ROOT}/os_linux"    ;;
    Darwin*)      C_DBX_OS="Mac"     ; C_DBX_INIT_PATH="${C_DBX_INIT_PATH_ROOT}/os_darwin"   ;;
    CYGWIN*)      C_DBX_OS="Cygwin"  ; C_DBX_INIT_PATH="${C_DBX_INIT_PATH_ROOT}/os_win64"    ;;
    MINGW*)       C_DBX_OS="Windows" ; C_DBX_INIT_PATH="${C_DBX_INIT_PATH_ROOT}/os_win64"    ;;
    *Msys)        C_DBX_OS="Windows" ; C_DBX_INIT_PATH="${C_DBX_INIT_PATH_ROOT}/os_win64"    ;;
    *)            C_DBX_OS="???:${unameOut}"
  esac

  echo "------------------------------------------------------------------------------------------------------------------";
  echo "Welcome to ${C_DBX_META_TEAM}/${C_DBX_META_TEAM_ID} DevBox-Shell v${C_DBX_META_VERSION} | See DEVBOX.md for tips and tasks on using this terminal ...";
  echo "------------------------------------------------------------------------------------------------------------------";
  #
  # check devbox core requirements and differ between project and standalone mode
  # --
  if [ ! -f "$C_DBX_INIT_PATH_ROOT/../$C_DBX_INIT_ENTRYPOINT" ]
  then
    echo "ERROR : devbox init-path not found, therefore devbox couldn't bootstrap baseline config. Check devbox integration first!"
    echo "LINK  : https://gitlab.bare.pandrosion.org/edp/infrastructure/cloud/managed-gcp/cloud-mgmt/ops-devbox-shell"
    exit 1
  else
    echo "◼︎ check : devbox init script available ✔︎"
  fi

  # ***
  # *** @TBD: add os specific init scripts (currently not implemented yet)
  # ***
  # --
  # echo "◼︎ check : init os-related bootstrap scripts at [./${C_DBX_INIT_PATH}] for [${C_DBX_OS}] ✔"

  #
  # check ansible installation/availability
  # --
  if ! command -v ansible &> /dev/null
  then
    echo "ERROR : local ansible binary not available, check required packages/setup first!"
    echo "LINK  : https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html"
    exit 1
  else
    echo "◼︎ check : ansible-cli/core is available ✔︎"
  fi
}

#
# function: print out some useful information after devbox init-phase
# --
init_print_help () {
  echo "------------------------------------------------------------------------------------------------------------------";
  echo "Available scripts (excerpt)"
  echo "------------------------------------------------------------------------------------------------------------------";
  echo "$ devbox run validate    | validate local dev environment for all requirements"
  echo "$ devbox run check-stage | check staging environment for availability (incl cloud-provider status)"
  echo "$ devbox run check-prod  | check production environment for availability (incl cloud-provider etc)"
  echo "$ devbox run sec-scan    | start a complete security scan for this app-stack (incl. secret-exposure check)"
  echo "$ devbox run img-scan    | start CVE testing/scanning for all app-stack images"
  echo "$ devbox run img-build   | build all app-stack images for local testing"
  echo "$ devbox run init-pyenv  | initialize a dedicated python3 environment (experimental featuren not required anymore)"
  echo "$ devbox run help        | print out devbox project documentation, show/describe all scripts available"
  echo "------------------------------------------------------------------------------------------------------------------";
  echo "type 'devbox run help' (or <your-dbx-run-alias> help) to show scripts/doc/dbx_main.md devbox-shell documentation"
  echo "type 'exit' to close this shell and return to your os-source terminal | os-shell"
  if [ -f "$C_DBX_INIT_SESSION_FILE_MARKER" ]; then
    echo "------------------------------------------------------------------------------------------------------------------";
    echo -e "You are in an active tmux session; use tmux-command (\033[37mcontrol+b\033[0m) <\033[34marrow-up\033[0m>|<\033[34marrow-down\033[0m> to switch between your"
    echo "active panes. The first pane will be on the top of your screen and handle all devbox shell commands. The second"
    echo "and 3rd pane will be on the bottom you your screen and handle tunnel-connection to ice-api & k8s-api etc."
  fi
  if cmp --silent -- $C_DBX_INIT_LOCAL_CONFIG_FILE $C_DBX_INIT_LOCAL_CONFIG_FILE_TEMPLATE ; then
      echo -e "\033[0m------------------------------------------------------------------------------------------------------------------"
      echo -e "\033[33m@INFO\033[0m: Currently you are using a simple copy of the default configuration for this devbox shell."
      echo -e "You can make your own adjustments to the resulting '\033[34m$C_DBX_INIT_LOCAL_CONFIG_FILE\033[0m' file at any time to"
      echo -e "customise the shell according to your needs. Check official reference information at:"
      echo -e "\033[37mhttps://www.jetify.com/devbox/docs/configuration/\033[0m"
      echo -e "\033[0m------------------------------------------------------------------------------------------------------------------"
  fi
  echo -e "\n"
}

init_pyenv () {
  echo "------------------------------------------------------------------------------------------------------------------";
  echo "Activate Python3 vENV"
  echo "------------------------------------------------------------------------------------------------------------------";
  python3 -m venv .venv
  source .venv/bin/activate
}

#
# shell entrypoint(s)
# --

init_check
init_print_help

