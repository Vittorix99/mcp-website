"use client"

import { useUser } from "@/contexts/userContext"
import { motion } from "framer-motion"
import { User, Settings, FileText, Calendar } from "lucide-react"

export default function AdminDashboard() {
  const { user } = useUser()

  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  const stagger = {
    animate: {
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  return (
    <motion.div initial="initial" animate="animate" variants={stagger} className="container mx-auto px-4 py-8 pt-20">
      <motion.h1 className="text-5xl font-bold gradient-text mb-6" variants={fadeInUp}>
        Admin Dashboard
      </motion.h1>
      <motion.p className="text-gray-300 text-xl mb-8" variants={fadeInUp}>
        Welcome, {user?.email || "Admin"}!
      </motion.p>
      <motion.div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" variants={fadeInUp}>
        <DashboardCard
          title="User Management"
          icon={<User className="h-8 w-8 text-mcp-orange" />}
          description="Manage user accounts and permissions"
        />
        <DashboardCard
          title="Event Settings"
          icon={<Settings className="h-8 w-8 text-mcp-orange" />}
          description="Configure event details and settings"
        />
        <DashboardCard
          title="Content Management"
          icon={<FileText className="h-8 w-8 text-mcp-orange" />}
          description="Update website content and blog posts"
        />
        <DashboardCard
          title="Event Calendar"
          icon={<Calendar className="h-8 w-8 text-mcp-orange" />}
          description="View and manage upcoming events"
        />
      </motion.div>
    </motion.div>
  )
}

function DashboardCard({ title, icon, description }) {
  return (
    <motion.div
      className="bg-black/50 p-6 rounded-lg shadow-lg border border-mcp-orange/20 hover:border-mcp-orange/50 transition-all duration-300"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      <div className="flex items-center mb-4">
        {icon}
        <h2 className="text-xl font-semibold text-white ml-3">{title}</h2>
      </div>
      <p className="text-gray-400">{description}</p>
    </motion.div>
  )
}

