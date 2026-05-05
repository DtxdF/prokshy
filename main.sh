#!/bin/sh

ETCDIR="/usr/local/etc/prokshy"
CMDDIR="${ETCDIR}/command.d"

while :; do
    read -r CMD

    if ! printf "%s" "${CMD}" | grep -qEe '^[a-zA-Z0-9_.-]+$'; then
        continue
    fi

    if [ ! -x "${CMDDIR}/${CMD}" ]; then
        continue
    fi

    read -r -t 1 ARG

    printf "%s" "${ARG}" | "${CMDDIR}/${CMD}"
done
