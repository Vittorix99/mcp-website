import Link from 'next/link'
import { routes } from '@/config/routes'

export default function ErrorPage() {
  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-orange-500 mb-4">Oops! Something went wrong</h1>
        <p className="text-orange-200 mb-8">We're sorry, but an error occurred. Please try again later.</p>
        <Link 
          href={routes.home}
          className="bg-orange-500 hover:bg-orange-600 text-black font-bold py-2 px-4 rounded transition duration-300"
        >
          Return to Home
        </Link>
      </div>
    </div>
  )
}