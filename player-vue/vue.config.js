module.exports = {
  devServer: {
    proxy: {
      "^/api": {
        target: "http://192.168.2.178:8000",
         changeOrigin: true,
        pathRewrite: { "^/api": "" },
        onProxyRes: function(proxyRes) {
          proxyRes.headers["x-accel-buffering"] = "no";
        }
      }
    }
  }
};
