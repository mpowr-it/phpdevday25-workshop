# OpenResty base
FROM openresty/openresty:1.25.3.2-alpine

ENV C_SERVICE_NAME_LONG="mpowr-labs/nginx/test-app-lua-db" \
    C_SERVICE_VERSION="openresty:1.25.3.2-alpine" \
    C_SERVICE_OS="alpine" \
    C_MESSAGE="stay awhile & listen my friend!" \
    C_APP_VERSION="1.0.8" \
    SKIP_TRACK=1

# Utilities + CA bundle
RUN apk add --no-cache ca-certificates curl wget perl mc postgresql-libs && update-ca-certificates

# Install Lua libs with OPM (TLS + templating + pg)
RUN /usr/local/openresty/bin/opm get fffonion/lua-resty-openssl \
 && /usr/local/openresty/bin/opm get bungle/lua-resty-template \
 && /usr/local/openresty/bin/opm get leafo/pgmoon

# Create nginx user/group (Alpine)
RUN addgroup -S nginx && adduser -S -G nginx -H -s /sbin/nologin nginx

# Config + site payload
RUN mkdir -p /usr/local/openresty/nginx/conf/conf.d /.docker/logs
COPY etc/nginx/nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY etc/nginx/conf.d/default.conf /usr/local/openresty/nginx/conf/conf.d/default.conf
COPY payload/ /usr/share/nginx/html
COPY tpl/30-meta-information-load.sh /docker-entrypoint.d/

# Permissions (use OpenResty log dir)
RUN chown -R nginx:nginx /usr/share/nginx/html \
 && mkdir -p /usr/local/openresty/nginx/logs /.docker \
 && chown -R nginx:nginx /usr/local/openresty/nginx/logs /.docker

# Build info
RUN printf "_docker/build/info     : image created [%s] -> service [${C_SERVICE_NAME_LONG}]\n" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> /.docker/.build_info \
 && echo   "_system/core/os        : $(uname -a)" >> /.docker/.build_info \
 && echo   "_system/backbone/os    : ${C_SERVICE_OS}" >> /.docker/.build_info \
 && echo   "_system/usr/grp/build  : $(whoami):$(whoami)" >> /.docker/.build_info \
 && rm -rf /var/cache/apk/*

LABEL maintainer="patrick.paechnatz@mpowr.it" \
      com.container.vendor="MPOWR IT GmbH" \
      com.container.os="${C_SERVICE_OS}" \
      com.container.service="${C_SERVICE_NAME_LONG}" \
      com.container.service.version="${C_SERVICE_VERSION}" \
      com.container.app.version="${C_APP_VERSION}" \
      img.name="mpowr-labs/web-app-lua" \
      img.description="ops-sandbox, mpowr-labs static web application (incl pgsql support)."
