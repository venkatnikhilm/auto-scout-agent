"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Monitor, Clock, Target, Link, AlertCircle } from "lucide-react"

interface MonitorResponse {
  message: string
  monitor_id: string
  interval: number
  parsed: {
    description?: string
    condition?: string
    interval?: string
    url?: string
  }
}

export default function AutoScoutLanding() {
  const [description, setDescription] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [response, setResponse] = useState<MonitorResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!description.trim()) return

    setIsLoading(true)
    setError(null)
    setResponse(null)

    try {
      const res = await fetch("http://127.0.0.1:8000/create_monitor", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ description: description.trim() }),
      })

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const data = await res.json()
      setResponse(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create monitor")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Monitor className="h-6 w-6 text-primary" />
              <span className="text-xl font-semibold text-foreground">AutoScout</span>
            </div>
            <Badge variant="secondary" className="text-xs">
              Beta
            </Badge>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto text-center space-y-8">
          {/* Hero Section */}
          <div className="space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold text-foreground text-balance">
              AutoScout – Smart Website Monitor
            </h1>
            <p className="text-lg text-muted-foreground text-pretty leading-relaxed">
              Describe what you want to track, we'll handle the rest.
            </p>
          </div>

          {/* Form Card */}
          <Card className="shadow-lg border-border/50">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl">Start Monitoring</CardTitle>
              <CardDescription>Tell us what you'd like to track and we'll set it up automatically</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Input
                    type="text"
                    placeholder="Track the price of this Nike hoodie every 60 seconds and notify me when it's less than $100"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="min-h-[60px] text-base leading-relaxed"
                    disabled={isLoading}
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full h-12 text-base font-medium"
                  disabled={isLoading || !description.trim()}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating Monitor...
                    </>
                  ) : (
                    "Start Monitoring"
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Error Display */}
          {error && (
            <Card className="border-destructive/50 bg-destructive/5">
              <CardContent className="pt-6">
                <p className="text-destructive text-sm">
                  <strong>Error:</strong> {error}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Response Display */}
          {response && (
            <Card className="border-primary/20 bg-primary/5 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-primary">
                  <Target className="h-5 w-5" />
                  {response.message}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        Monitor ID
                      </Badge>
                    </div>
                    <p className="font-mono text-sm bg-muted p-2 rounded border">{response.monitor_id}</p>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <Badge variant="outline" className="text-xs">
                        Check Interval
                      </Badge>
                    </div>
                    <p className="text-sm bg-muted p-2 rounded border">Every {response.interval} seconds</p>
                  </div>
                </div>

                {response.parsed && Object.keys(response.parsed).length > 0 && (
                  <div className="space-y-2">
                    <Badge variant="outline" className="text-xs">
                      Extracted Information
                    </Badge>
                    <div className="bg-muted p-4 rounded border space-y-3">
                      {response.parsed.description && (
                        <div className="space-y-1">
                          <span className="text-sm font-medium text-muted-foreground">Description:</span>
                          <p className="text-sm bg-background p-2 rounded border">{response.parsed.description}</p>
                        </div>
                      )}
                      {response.parsed.url && (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <Link className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium text-muted-foreground">URL:</span>
                          </div>
                          <p className="text-sm font-mono bg-background p-2 rounded border break-all">
                            {response.parsed.url}
                          </p>
                        </div>
                      )}
                      {response.parsed.condition && (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <AlertCircle className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium text-muted-foreground">Condition:</span>
                          </div>
                          <p className="text-sm bg-background p-2 rounded border">{response.parsed.condition}</p>
                        </div>
                      )}
                      {response.parsed.interval && (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium text-muted-foreground">Requested Interval:</span>
                          </div>
                          <p className="text-sm bg-background p-2 rounded border">{response.parsed.interval}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Features Section */}
          <div className="pt-8 grid gap-6 md:grid-cols-3">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto">
                <Monitor className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-semibold">Smart Parsing</h3>
              <p className="text-sm text-muted-foreground">
                AI-powered extraction of monitoring parameters from natural language
              </p>
            </div>
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto">
                <Clock className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-semibold">Real-time Tracking</h3>
              <p className="text-sm text-muted-foreground">Continuous monitoring with customizable check intervals</p>
            </div>
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto">
                <Target className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-semibold">Instant Alerts</h3>
              <p className="text-sm text-muted-foreground">Get notified immediately when your conditions are met</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
