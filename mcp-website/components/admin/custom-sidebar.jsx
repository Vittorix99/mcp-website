"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Home, Calendar, Ticket, CreditCard,
  MessageSquare, Image, Send, Settings,
  Users, LayoutList, ChevronRight, ToggleLeft, AlertTriangle,
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
      { title: "Eventi",      url: routes.admin.events,       icon: Calendar  },
      { title: "Acquisti",    url: routes.admin.purchases,    icon: Ticket    },
      { title: "Tessere",     url: routes.admin.memberships,  icon: CreditCard },
      { title: "Foto Eventi", url: routes.admin.eventsPhotos, icon: Image     },
    ],
  },
  {
    title: "Comunicazioni",
    items: [
      { title: "Messaggi", url: routes.admin.messages, icon: MessageSquare },
      {
        title: "Sender",
        url: routes.admin.sender.campaigns,
        icon: Send,
        children: [
          { title: "Campagne",    url: routes.admin.sender.campaigns,    icon: LayoutList  },
          { title: "CRM",         url: routes.admin.sender.subscribers,  icon: Users       },
          { title: "Opt In/Out",  url: routes.admin.sender.optinOptout,  icon: ToggleLeft  },
        ],
      },
    ],
  },
  {
    title: "Impostazioni",
    items: [
      { title: "Settings", url: routes.admin.settings, icon: Settings },
      { title: "Error Logs", url: routes.admin.errorLogs, icon: AlertTriangle },
    ],
  },
]

export function CustomSidebar() {
  const pathname = usePathname()

  const isActive = (url) =>
    url !== routes.admin.dashboard
      ? pathname.startsWith(url)
      : pathname === url

  return (
    <Sidebar className="border-r border-neutral-800 gradient-text custom-sidebar">
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
            <h4 className="px-4 text-xs font-semibold text-neutral-500 uppercase tracking-wide">
              {section.title}
            </h4>
            <SidebarMenu className="mt-1 p-2">
              {section.items.map((item) => {
                const active = isActive(item.url)
                const hasChildren = item.children?.length > 0
                const childActive = hasChildren && item.children.some((c) => isActive(c.url))
                const expanded = active || childActive

                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={active && !hasChildren}
                      tooltip={item.title}
                      className={`group transition-colors duration-200 ${
                        (active && !hasChildren) || childActive
                          ? "bg-orange-500/10 text-orange-400"
                          : "text-neutral-300 hover:text-orange-400"
                      }`}
                    >
                      <Link href={item.url} className="flex items-center w-full">
                        <item.icon className="h-5 w-5 mr-2 group-hover:scale-105 transition-transform duration-150" />
                        <span className="flex-1">{item.title}</span>
                        {hasChildren && (
                          <ChevronRight
                            className={`h-3.5 w-3.5 transition-transform duration-200 ${expanded ? "rotate-90" : ""}`}
                          />
                        )}
                      </Link>
                    </SidebarMenuButton>

                    {/* Sub-items */}
                    {hasChildren && expanded && (
                      <div className="ml-4 mt-0.5 border-l border-neutral-800 pl-2 space-y-0.5">
                        {item.children.map((child) => {
                          const childIsActive = isActive(child.url)
                          return (
                            <Link
                              key={child.title}
                              href={child.url}
                              className={`flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors duration-150 ${
                                childIsActive
                                  ? "text-orange-400 bg-orange-500/10"
                                  : "text-neutral-400 hover:text-orange-400"
                              }`}
                            >
                              <child.icon className="h-4 w-4 shrink-0" />
                              {child.title}
                            </Link>
                          )
                        })}
                      </div>
                    )}
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
