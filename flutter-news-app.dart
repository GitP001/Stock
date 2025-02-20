import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );
  runApp(const NewsApp());
}

class NewsApp extends StatelessWidget {
  const NewsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'News App',
      theme: ThemeData.dark(),
      home: const NewsHomePage(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class NewsArticle {
  final String id;
  final String imageUrl;
  final String title;
  final String summary;
  final String source;
  final String readTime;

  NewsArticle({
    required this.id,
    required this.imageUrl,
    required this.title,
    required this.summary,
    required this.source,
    required this.readTime,
  });
}

class NewsHomePage extends StatefulWidget {
  const NewsHomePage({super.key});

  @override
  State<NewsHomePage> createState() => _NewsHomePageState();
}

class _NewsHomePageState extends State<NewsHomePage> {
  int _selectedIndex = 0;
  final PageController _pageController = PageController();

  final List<NewsArticle> articles = [
    NewsArticle(
      id: '1',
      imageUrl: 'https://example.com/image1.jpg',
      title: 'Two rings crafted from one billion-year-old natural diamond: Tanishq',
      summary: "This Valentine's Day, celebrate your eternal bond with the Soulmate Diamond Pair by Tanishq. Two rings crafted from one billion year-old-natural diamond, these rings symbolise a journey of shared togetherness and an everlasting bond. A billion years in the making, to embody a timeless love.",
      source: 'Tanishq',
      readTime: '2 min read',
    ),
    NewsArticle(
      id: '2',
      imageUrl: 'https://example.com/image2.jpg',
      title: 'Global Climate Summit Announces Breakthrough Agreement',
      summary: 'World leaders reach historic consensus on ambitious climate action goals, setting new standards for environmental protection and sustainable development.',
      source: 'World News',
      readTime: '3 min read',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Main Content
          PageView.builder(
            controller: _pageController,
            scrollDirection: Axis.vertical,
            itemCount: articles.length,
            itemBuilder: (context, index) {
              return ArticleCard(article: articles[index]);
            },
          ),

          // Navigation Bar
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              height: 83,
              decoration: BoxDecoration(
                color: Colors.black,
                border: Border(
                  top: BorderSide(
                    color: Colors.grey[900]!,
                    width: 0.5,
                  ),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildNavItem(0, Icons.home, 'Home'),
                  _buildNavItem(1, Icons.grid_view, 'Categories'),
                  _buildNavItem(2, Icons.person, 'Profile'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, String label) {
    return InkWell(
      onTap: () => setState(() => _selectedIndex = index),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: _selectedIndex == index ? Colors.white : Colors.grey,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: _selectedIndex == index ? Colors.white : Colors.grey,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class ArticleCard extends StatelessWidget {
  final NewsArticle article;

  const ArticleCard({super.key, required this.article});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 844,
      width: 390,
      color: Colors.black,
      child: Stack(
        children: [
          // Image Section
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            height: 380,
            child: Hero(
              tag: article.id,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  Image.network(
                    article.imageUrl,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) {
                      return Container(
                        color: Colors.grey[900],
                        child: const Icon(Icons.image, size: 50),
                      );
                    },
                  ),
                  Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.black.withOpacity(0.7),
                          Colors.transparent,
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Content Section
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            height: 464,
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.black,
                    Colors.grey[900]!,
                  ],
                ),
              ),
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    article.title,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    article.summary,
                    style: const TextStyle(
                      fontSize: 18,
                      color: Colors.white70,
                      height: 1.5,
                    ),
                  ),
                  const Spacer(),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        article.source,
                        style: TextStyle(
                          color: Colors.grey[400],
                          fontSize: 14,
                        ),
                      ),
                      Text(
                        article.readTime,
                        style: TextStyle(
                          color: Colors.grey[400],
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Interaction Buttons
          Positioned(
            right: 16,
            bottom: 120,
            child: Column(
              children: [
                _buildInteractionButton(Icons.share),
                const SizedBox(height: 16),
                _buildInteractionButton(Icons.bookmark_border),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInteractionButton(IconData icon) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        shape: BoxShape.circle,
      ),
      child: IconButton(
        icon: Icon(icon),
        color: Colors.white,
        onPressed: () {},
      ),
    );
  }
}
