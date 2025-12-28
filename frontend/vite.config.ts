import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  server: {
    port: 5173,
    strictPort: true,   // <-- THIS forces 5173, no auto-increment
    host: "0.0.0.0",
    fs: {
      // allow serving files from the project root and the data/addons folder
      allow: [path.resolve(__dirname), path.resolve(__dirname, '../data/addons')],
    },
  },
  plugins: [react()],
  resolve: {
    // Force resolving react to the frontend's node_modules so files outside the frontend
    // (like addons under `data/addons`) can import the same React instance.
    alias: {
      react: path.resolve(__dirname, 'node_modules/react'),
      'react-dom': path.resolve(__dirname, 'node_modules/react-dom'),
      'react/jsx-runtime': path.resolve(__dirname, 'node_modules/react/jsx-runtime'),
    },
    dedupe: ['react', 'react-dom'],
  },
  optimizeDeps: {
    include: ['react/jsx-runtime'],
  },
})
