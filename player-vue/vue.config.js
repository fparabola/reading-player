module.exports = {
  devServer: {
    proxy: {
      "^/api": {
        target: "http://localhost:8000",
         changeOrigin: true,
        pathRewrite: { "^/api": "" },
        onProxyRes: function(proxyRes) {
          proxyRes.headers["x-accel-buffering"] = "no";
        }
      }
    }
  }
};
