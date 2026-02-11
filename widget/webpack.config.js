const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
  entry: "./src/chatbot-widget.ts",
  output: {
    filename: "chatbot.js",
    path: path.resolve(__dirname, "dist"),
    library: "LKClinicWidget",
    libraryTarget: "umd",
  },
  resolve: {
    extensions: [".ts", ".js"],
  },
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: "ts-loader",
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, "css-loader"],
      },
    ],
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: "chatbot.css",
    }),
  ],
  performance: {
    maxEntrypointSize: 51200, // 50KB
    maxAssetSize: 51200,
    hints: "warning",
  },
};
