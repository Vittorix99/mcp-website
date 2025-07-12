"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Home, Calendar, Ticket, CreditCard,
  MessageSquare, Mail, Image, Layers, UserPlus
} from "lucide-react"
import "@/app/style/admin.css"

import { routes } from "@/config/routes"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarFooter,
  SidebarRail,
} from "@/components/ui/sidebar"

const navigationSections = [
  {
    title: "Generale",
    items: [
      { title: "Dashboard", url: routes.admin.dashboard, icon: Home },
    ],
  },
  {
    title: "Gestione",
    items: [
      { title: "Eventi", url: routes.admin.events, icon: Calendar },
      { title: "Acquisti", url: routes.admin.purchases, icon: Ticket },
      { title: "Tessere", url: routes.admin.memberships, icon: CreditCard },
      { title: "Foto Eventi", url: routes.admin.eventsPhotos, icon: Image },

    ],
  },
  {
    title: "Comunicazioni",
    items: [
      { title: "Messaggi", url: routes.admin.messages, icon: MessageSquare },
      { title: "Newsletter", url: routes.admin.newsletter, icon: Mail },
    ],
  },
  {
    title: "Impostazioni",
    items: [
      { title: "Settings", url: routes.admin.settings, icon: Layers },
    ],
  },
]

export function CustomSidebar() {
  const pathname = usePathname()

  return (
    <Sidebar className="border-r border-neutral-800 gradient-text  custom-sidebar">
      <SidebarHeader className="admin-header">
        <SidebarMenu className="mt-3">
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <Link href={routes.home}>
                <span className="text-2xl font-bold tracking-tight gradient-text">MCP Admin</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent className="custom-sidebar">
        {navigationSections.map((section) => (
          <div key={section.title} className="mt-6">
            <h4 className="px-4 text-xs font-semibold text-neutral-500 uppercase tracking-wide">{section.title}</h4>
            <SidebarMenu className="mt-1 p-2">
              {section.items.map((item) => {
                const isActive = pathname === item.url
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.title}
                      className={`group transition-colors duration-200 ${
                        isActive ? "bg-orange-500/10 text-orange-400" : "text-neutral-300 hover:text-orange-400"
                      }`}
                    >
                      <Link href={item.url}>
                        <item.icon className="h-5 w-5 mr-2 group-hover:scale-105 transition-transform duration-150" />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </div>
        ))}
      </SidebarContent>

      <SidebarRail />
    </Sidebar>
  )
}