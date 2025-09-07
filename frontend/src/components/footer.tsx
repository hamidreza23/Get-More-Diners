import Link from "next/link"
import { DineBoostLogo } from "@/components/logos/dineboost-logo"

export function Footer() {
  return (
    <footer className="bg-gray-800 text-white">
      <div className="mx-auto max-w-6xl px-4 py-16">
        <div className="grid gap-12 md:grid-cols-4">
          <div className="md:col-span-1">
            <div className="flex items-center gap-3">
              <DineBoostLogo />
              <h2 className="text-white text-2xl font-bold">DineBoost</h2>
            </div>
            <p className="mt-4 text-gray-400">The modern way to market your restaurant.</p>
          </div>
          <div>
            <h3 className="text-lg font-semibold">Product</h3>
            <ul className="mt-4 space-y-3">
              <li>
                <Link href="#features" className="text-gray-400 hover:text-white transition-colors duration-300">
                  Features
                </Link>
              </li>
              <li>
                <Link href="#pricing" className="text-gray-400 hover:text-white transition-colors duration-300">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
                  Integrations
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
                  Updates
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold">Company</h3>
            <ul className="mt-4 space-y-3">
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
                  About Us
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
                  Careers
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
                  Blog
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
                  Contact Us
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold">Resources</h3>
            <ul className="mt-4 space-y-3">
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
                  Help Center
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
                  Privacy Policy
                </Link>
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-16 flex flex-col items-center border-t border-gray-700 pt-8 sm:flex-row sm:justify-between">
          <p className="text-gray-400">© 2024 DineBoost. All rights reserved.</p>
          <div className="mt-4 flex gap-6 sm:mt-0">
            <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
              <svg aria-hidden="true" className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path
                  clipRule="evenodd"
                  d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z"
                  fillRule="evenodd"
                ></path>
              </svg>
            </Link>
            <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
              <svg aria-hidden="true" className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.71v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"></path>
              </svg>
            </Link>
            <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
              <svg aria-hidden="true" className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path
                  clipRule="evenodd"
                  d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm4.94 6.94a.75.75 0 010 1.06L13.06 14.94a.75.75 0 11-1.06-1.06l3.94-3.94a.75.75 0 011.06 0zM12 12.75a.75.75 0 01.75-.75h.008a.75.75 0 01.75.75v.008a.75.75 0 01-.75.75h-.008a.75.75 0 01-.75-.75v-.008zM12 15.75a.75.75 0 01.75-.75h.008a.75.75 0 01.75.75v.008a.75.75 0 01-.75.75h-.008a.75.75 0 01-.75-.75v-.008zM9.06 10.94a.75.75 0 11-1.06 1.06L7.06 11a.75.75 0 011.06-1.06l.94.94z"
                  fillRule="evenodd"
                ></path>
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
