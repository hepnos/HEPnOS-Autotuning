# Simple function to download a git repo and set
# it to a given reference (commit, branch, or tag)

function download_from_git {
    NAME=$1
    URL=$2
    REF=$3
    log "Cloning $NAME repo ($URL)..."
    git clone $URL
    log "Checking out $REF..."
    pushd $NAME
    git checkout $REF
    popd
}
