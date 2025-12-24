

#  AI Voice SaaS Platform

An AI-powered Voice-as-a-Service (VaaS) platform that allows users to generate, clone, and manage high-quality AI voices. Built with performance, scalability, and user experience in mind.


##  Overview

**AIVoiceSaas** is a comprehensive solution for creators, developers, and businesses to leverage AI voice technology. From professional Text-to-Speech (TTS) to advanced Voice Cloning, this platform provides an intuitive dashboard to manage audio assets and subscriptions.

##  Features

- **Text-to-Speech (TTS):** Convert text into lifelike speech using state-of-the-art models (OpenAI, ElevenLabs).
- **Voice Cloning:** Create digital clones of your own voice with just a few minutes of audio.
- **AI Audio Editing:** Fine-tune pitch, stability, and clarity of generated audio.
- **User Dashboard:** Manage your audio projects, credits, and history.
- **Subscription Management:** Tiered pricing plans integrated with **Stripe**.
- **Secure Authentication:** Robust user login and profile management via **Clerk** or **NextAuth**.
- **Dark/Light Mode:** Seamless UI experience with Tailwind CSS.

##  Tech Stack

- **Frontend:** [Next.js 14](https://nextjs.org/) (App Router), [Tailwind CSS](https://tailwindcss.com/), [Shadcn/UI](https://ui.shadcn.com/)
- **Backend:** Next.js Server Actions, [Node.js](https://nodejs.org/)
- **Database:** [PostgreSQL](https://www.postgresql.org/) with [Prisma ORM](https://www.prisma.io/)
- **AI Engines:** [ElevenLabs API](https://elevenlabs.io/), [OpenAI Whisper/TTS](https://openai.com/)
- **Payments:** [Stripe](https://stripe.com/)
- **Authentication:** [Clerk](https://clerk.com/) / [NextAuth.js](https://next-auth.js.org/)
- **File Storage:** [UploadThing](https://uploadthing.com/) / AWS S3

##  Getting Started

### Prerequisites

- Node.js 18.x or later
- A package manager (npm, yarn, or pnpm)
- API Keys for: ElevenLabs, OpenAI, Stripe, and Clerk.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rameshramaswamy/AIVoiceSaas.git
   cd AIVoiceSaas
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Environment Variables:**
   Create a `.env.local` file in the root directory and add your credentials:
   ```env
   # App
   NEXT_PUBLIC_APP_URL=http://localhost:3000

   # Database
   DATABASE_URL="postgresql://user:password@localhost:5432/aivoice"

   # Auth (Clerk Example)
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
   CLERK_SECRET_KEY=...

   # AI APIs
   ELEVENLABS_API_KEY=...
   OPENAI_API_KEY=...

   # Payments
   STRIPE_API_KEY=...
   STRIPE_WEBHOOK_SECRET=...
   ```

4. **Database Setup:**
   ```bash
   npx prisma generate
   npx prisma db push
   ```

5. **Run the development server:**
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) to see your app.

##  Project Structure

```text
├── app/              # Next.js App Router (Pages & API)
├── components/       # Reusable React components
├── lib/              # Utility functions and shared logic (Prisma, Stripe, AI)
├── hooks/            # Custom React hooks
├── public/           # Static assets
├── prisma/           # Database schema
└── types/            # TypeScript interfaces
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



---
*Developed by [Ramesh Ramaswamy](https://github.com/rameshramaswamy)*
