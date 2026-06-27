import { supabase } from './supabase'
import { ClerkProvider } from './auth'

export default function App() {
  return (
    <ClerkProvider>
      <div>My App</div>
    </ClerkProvider>
  )
}
